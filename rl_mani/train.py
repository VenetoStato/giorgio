"""PPO (implementazione compatta, torch) per OrcaCubeEnv su GPU.

Uso:  python train.py --envs 4096 --iters 3000 --out runs/r1
Scrive: <out>/log.csv (una riga per iterazione), <out>/modello.pt (ultimo),
        <out>/modello_iniziale.pt (politica non addestrata), <out>/modello_<iter>.pt (pochi).
"""
import argparse
import csv
import os
import time
import torch
import torch.nn as nn

from env_orca import OrcaCubeEnv


class Normalizzatore(nn.Module):
    def __init__(self, dim, eps=1e-4):
        super().__init__()
        self.register_buffer("mean", torch.zeros(dim))
        self.register_buffer("var", torch.ones(dim))
        self.register_buffer("count", torch.tensor(eps))

    @torch.no_grad()
    def update(self, x):
        bm, bv, bc = x.mean(0), x.var(0, unbiased=False), x.shape[0]
        delta = bm - self.mean
        tot = self.count + bc
        self.mean += delta * bc / tot
        self.var = (self.var * self.count + bv * bc + delta ** 2 * self.count * bc / tot) / tot
        self.count = tot

    def forward(self, x):
        return ((x - self.mean) / torch.sqrt(self.var + 1e-8)).clamp(-5, 5)


def mlp(i, o, h=(512, 256, 128)):
    layers, d = [], i
    for k in h:
        layers += [nn.Linear(d, k), nn.ELU()]
        d = k
    layers.append(nn.Linear(d, o))
    return nn.Sequential(*layers)


class AttoreCritico(nn.Module):
    def __init__(self, od, ad, std0=0.6):
        super().__init__()
        self.norm = Normalizzatore(od)
        self.pi = mlp(od, ad)
        self.v = mlp(od, 1)
        self.log_std = nn.Parameter(torch.full((ad,), float(torch.log(torch.tensor(std0)))))
        with torch.no_grad():
            self.pi[-1].weight.mul_(0.01)
            self.pi[-1].bias.zero_()

    def dist(self, o):
        mu = self.pi(self.norm(o))
        return torch.distributions.Normal(mu, self.log_std.exp().expand_as(mu))

    def value(self, o):
        return self.v(self.norm(o)).squeeze(-1)

    @torch.no_grad()
    def act_det(self, o):
        return self.pi(self.norm(o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envs", type=int, default=4096)
    ap.add_argument("--iters", type=int, default=3000)
    ap.add_argument("--horizon", type=int, default=24)
    ap.add_argument("--out", default="runs/r1")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--minibatch", type=int, default=4)
    ap.add_argument("--max_minutes", type=float, default=200)
    ap.add_argument("--resume", default="")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    torch.manual_seed(a.seed)

    env = OrcaCubeEnv(a.envs, seed=a.seed)
    dev = env.dev
    ac = AttoreCritico(env.obs_dim, env.act_dim).to(dev)
    if a.resume:
        ac.load_state_dict(torch.load(a.resume, map_location=dev)["modello"])
    opt = torch.optim.Adam(ac.parameters(), lr=a.lr)
    lr = a.lr
    gamma, lam, clip, kl_t = 0.99, 0.95, 0.2, 0.016
    N, H = a.envs, a.horizon

    def salva(path, it, steps):
        torch.save({"modello": ac.state_dict(), "iter": it, "passi": steps,
                    "obs_dim": env.obs_dim, "act_dim": env.act_dim}, path)

    salva(os.path.join(a.out, "modello_iniziale.pt"), 0, 0)
    obs = env.reset()
    buf_o = torch.zeros(H, N, env.obs_dim, device=dev)
    buf_a = torch.zeros(H, N, env.act_dim, device=dev)
    buf_lp = torch.zeros(H, N, device=dev)
    buf_r = torch.zeros(H, N, device=dev)
    buf_d = torch.zeros(H, N, device=dev)
    buf_v = torch.zeros(H, N, device=dev)

    f = open(os.path.join(a.out, "log.csv"), "a" if a.resume else "w", newline="")
    w = csv.writer(f)
    if not a.resume:
        w.writerow(["iter", "passi", "tempo_s", "ricompensa_passo", "ritorno_episodio", "vel_rot_rad_s",
                    "rad_10s", "frac_cadute", "durata_ep_s", "std", "lr", "kl", "loss_v"])
    ep_ret = torch.zeros(N, device=dev)
    t0 = time.time()
    steps = 0
    for it in range(1, a.iters + 1):
        fin_ret, fin_rot, fin_t, fin_drop = [], [], [], []
        with torch.no_grad():
            for h in range(H):
                ac.norm.update(obs)
                dist = ac.dist(obs)
                act = dist.sample()
                buf_o[h], buf_a[h] = obs, act
                buf_lp[h] = dist.log_prob(act).sum(-1)
                buf_v[h] = ac.value(obs)
                obs, rew, done, timeout, info = env.step(act)
                # bootstrap sui timeout
                rew = rew + gamma * buf_v[h] * timeout.float()
                buf_r[h], buf_d[h] = rew, done.float()
                ep_ret += rew
                if done.any():
                    idx = done.nonzero().squeeze(-1)
                    fin_ret.append(ep_ret[idx])
                    fin_rot.append(info["rot_acc"][idx])
                    fin_t.append(info["t"][idx].float() * env.dt)
                    fin_drop.append(info["caduto"][idx].float())
                    ep_ret[idx] = 0
            last_v = ac.value(obs)
            adv = torch.zeros_like(buf_r)
            g = torch.zeros(N, device=dev)
            for h in reversed(range(H)):
                nv = last_v if h == H - 1 else buf_v[h + 1]
                nd = 1.0 - buf_d[h]
                delta = buf_r[h] + gamma * nv * nd - buf_v[h]
                g = delta + gamma * lam * nd * g
                adv[h] = g
            ret = adv + buf_v
        steps += N * H

        bo, ba, blp = buf_o.reshape(-1, env.obs_dim), buf_a.reshape(-1, env.act_dim), buf_lp.reshape(-1)
        badv, bret, bv = adv.reshape(-1), ret.reshape(-1), buf_v.reshape(-1)
        badv = (badv - badv.mean()) / (badv.std() + 1e-8)
        B = bo.shape[0]
        mb = B // a.minibatch
        kls, lvs = [], []
        for ep in range(a.epochs):
            perm = torch.randperm(B, device=dev)
            for k in range(a.minibatch):
                j = perm[k * mb:(k + 1) * mb]
                dist = ac.dist(bo[j])
                lp = dist.log_prob(ba[j]).sum(-1)
                ratio = torch.exp(lp - blp[j])
                s1 = ratio * badv[j]
                s2 = torch.clamp(ratio, 1 - clip, 1 + clip) * badv[j]
                lpi = -torch.min(s1, s2).mean()
                v = ac.value(bo[j])
                vc = bv[j] + (v - bv[j]).clamp(-clip, clip)
                lv = torch.max((v - bret[j]) ** 2, (vc - bret[j]) ** 2).mean()
                ent = dist.entropy().sum(-1).mean()
                loss = lpi + 1.0 * lv - 0.002 * ent
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(ac.parameters(), 1.0)
                opt.step()
                with torch.no_grad():
                    kl = (blp[j] - lp).mean().abs().item()
                    # KL approx (Schulman) più stabile
                    lr_ratio = lp - blp[j]
                    kl = ((torch.exp(lr_ratio) - 1) - lr_ratio).mean().item()
                kls.append(kl)
                lvs.append(lv.item())
                # lr adattivo su KL
                if kl > 2 * kl_t:
                    lr = max(1e-5, lr / 1.5)
                elif kl < kl_t / 2:
                    lr = min(1e-3, lr * 1.5)
                for pg in opt.param_groups:
                    pg["lr"] = lr
            with torch.no_grad():
                ac.log_std.clamp_(-2.5, 0.0)

        # statistiche
        el = time.time() - t0
        if fin_ret:
            R = torch.cat(fin_ret)
            rot = torch.cat(fin_rot)
            tt = torch.cat(fin_t)
            dr = torch.cat(fin_drop)
            vel = (rot / tt.clamp(min=env.dt)).mean().item()
            row = [it, steps, round(el, 1), round(buf_r.mean().item(), 4), round(R.mean().item(), 3),
                   round(vel, 4), round(vel * 10, 3), round(dr.mean().item(), 4), round(tt.mean().item(), 2)]
        else:
            row = [it, steps, round(el, 1), round(buf_r.mean().item(), 4), "", "", "", "", ""]
        row += [round(ac.log_std.exp().mean().item(), 4), f"{lr:.2e}", round(sum(kls) / len(kls), 5),
                round(sum(lvs) / len(lvs), 4)]
        w.writerow(row)
        f.flush()
        if it % 10 == 0 or it == 1:
            print(f"it {it} passi {steps/1e6:.1f}M t {el/60:.1f}min r/passo {row[3]} ritorno {row[4]} "
                  f"rad/10s {row[6]} cadute {row[7]} durata {row[8]} std {row[9]} lr {row[10]}", flush=True)
        if it % 50 == 0:
            salva(os.path.join(a.out, "modello.pt"), it, steps)
        if it in (100, 300, 1000):
            salva(os.path.join(a.out, f"modello_{it}.pt"), it, steps)
        if el > a.max_minutes * 60:
            print("limite di tempo raggiunto")
            break
    salva(os.path.join(a.out, "modello.pt"), it, steps)
    f.close()
    print("fine", it, steps, f"{(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
