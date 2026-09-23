#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旋转魔方 · 每层随机旋转 + 整体持续旋转 · 终端真彩色渲染
按 Ctrl+C 退出
"""

import math
import os
import random
import sys
import time

# ---------- 配置 ----------
W, H = 72, 32
CUBE_HALF = 0.47
FOCAL_TAN = 0.45
ROT_DURATION = 0.38
ROT_INTERVAL = (0.35, 0.9)

# 魔方六面颜色
COL_RED    = (1.00, 0.05, 0.05)
COL_ORANGE = (1.00, 0.45, 0.00)
COL_WHITE  = (0.95, 0.95, 0.95)
COL_YELLOW = (1.00, 0.95, 0.10)
COL_GREEN  = (0.05, 0.85, 0.15)
COL_BLUE   = (0.05, 0.25, 1.00)

# 内部面颜色（暗灰色，比之前亮很多，能看清）
INNER_R, INNER_G, INNER_B = 110, 110, 122


def mat_mul(A, B):
    a00, a01, a02 = A[0]; a10, a11, a12 = A[1]; a20, a21, a22 = A[2]
    b00, b01, b02 = B[0]; b10, b11, b12 = B[1]; b20, b21, b22 = B[2]
    return [
        [a00*b00 + a01*b10 + a02*b20, a00*b01 + a01*b11 + a02*b21, a00*b02 + a01*b12 + a02*b22],
        [a10*b00 + a11*b10 + a12*b20, a10*b01 + a11*b11 + a12*b21, a10*b02 + a11*b12 + a12*b22],
        [a20*b00 + a21*b10 + a22*b20, a20*b01 + a21*b11 + a22*b21, a20*b02 + a21*b12 + a22*b22],
    ]


def mat_vec(M, v):
    x, y, z = v
    return [
        M[0][0]*x + M[0][1]*y + M[0][2]*z,
        M[1][0]*x + M[1][1]*y + M[1][2]*z,
        M[2][0]*x + M[2][1]*y + M[2][2]*z,
    ]


def rot_axis(axis, ang):
    c = math.cos(ang); s = math.sin(ang)
    if axis == 0:
        return [[1, 0, 0], [0, c, -s], [0, s, c]]
    if axis == 1:
        return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def build_cube():
    cubes = []
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                f = [None] * 6
                if x ==  1: f[0] = COL_RED
                if x == -1: f[1] = COL_ORANGE
                if y ==  1: f[2] = COL_WHITE
                if y == -1: f[3] = COL_YELLOW
                if z ==  1: f[4] = COL_GREEN
                if z == -1: f[5] = COL_BLUE
                cubes.append({
                    'pos': [float(x), float(y), float(z)],
                    'rot': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    'faces': f,
                })
    return cubes


class RotationTask:
    def __init__(self, axis, direction, cubes, duration=ROT_DURATION):
        self.axis = axis
        self.direction = direction
        self.duration = duration
        self.elapsed = 0.0
        self.cubes = cubes
        self.init = [{'pos': list(c['pos']),
                      'rot': [list(r) for r in c['rot']]} for c in cubes]
        self.done = False

    def update(self, dt):
        self.elapsed += dt
        p = self.elapsed / self.duration
        if p > 1.0: p = 1.0
        e = p * p * (3.0 - 2.0 * p)
        ang = self.direction * e * (math.pi / 2.0)
        R = rot_axis(self.axis, ang)
        for i, c in enumerate(self.cubes):
            ini = self.init[i]
            c['pos'] = mat_vec(R, ini['pos'])
            c['rot'] = mat_mul(R, ini['rot'])
        if p >= 1.0:
            self.done = True
            for c in self.cubes:
                c['pos'] = [round(v) for v in c['pos']]


def make_camera():
    cam = (3.6, 2.6, 5.6)
    tgt = (0.0, 0.0, 0.0)
    fx = tgt[0] - cam[0]; fy = tgt[1] - cam[1]; fz = tgt[2] - cam[2]
    fl = math.sqrt(fx*fx + fy*fy + fz*fz)
    fx /= fl; fy /= fl; fz /= fl

    rx = -fz; ry = 0.0; rz = fx
    rl = math.sqrt(rx*rx + rz*rz)
    if rl < 1e-9:
        rx, ry, rz = 1.0, 0.0, 0.0
    else:
        rx /= rl; rz /= rl

    ux = ry*fz - rz*fy
    uy = rz*fx - rx*fz
    uz = rx*fy - ry*fx
    return cam, (fx, fy, fz), (rx, ry, rz), (ux, uy, uz)


def main():
    os.system('')
    sys.stdout.write('\033[2J\033[?25l')
    sys.stdout.flush()

    cam, fwd, right, up = make_camera()
    cam_x, cam_y, cam_z = cam
    fx, fy, fz = fwd
    rx, ry, rz = right
    ux, uy, uz = up

    aspect = W / (H * 2.0)
    tan_h = FOCAL_TAN

    ray_dirs = [None] * (W * H)
    for row in range(H):
        for col in range(W):
            sx = (2.0 * (col + 0.5) / W - 1.0) * tan_h * aspect
            sy = (1.0 - 2.0 * (row + 0.5) / H) * tan_h
            dx = fx + sx * rx + sy * ux
            dy = fy + sx * ry + sy * uy
            dz = fz + sx * rz + sy * uz
            dl = math.sqrt(dx*dx + dy*dy + dz*dz)
            ray_dirs[row * W + col] = (dx/dl, dy/dl, dz/dl)

    lx, ly, lz = 0.45, 0.85, 0.65
    ll = math.sqrt(lx*lx + ly*ly + lz*lz)
    lx /= ll; ly /= ll; lz /= ll

    cubes = build_cube()
    random.seed()
    t = 0.0
    next_rot = 0.4
    tasks = []
    last = time.time()
    BLOCK = '█'

    try:
        while True:
            now = time.time()
            dt = now - last
            last = now
            if dt > 0.15: dt = 0.15
            t += dt

            # 层旋转任务
            for task in tasks:
                task.update(dt)
            tasks = [tk for tk in tasks if not tk.done]

            if t >= next_rot and not tasks:
                axis = random.randint(0, 2)
                layer = random.choice((-1, 0, 1))
                direction = random.choice((-1, 1))
                sel = [c for c in cubes if round(c['pos'][axis]) == layer]
                if sel:
                    tasks.append(RotationTask(axis, direction, sel))
                next_rot = t + random.uniform(*ROT_INTERVAL)

            # ---------- 整体旋转 G = Ry(a) · Rx(b) ----------
            ga = t * 0.35
            gb = t * 0.22
            cga, sga = math.cos(ga), math.sin(ga)
            cgb, sgb = math.cos(gb), math.sin(gb)
            G = [
                [cga, sga*sgb, sga*cgb],
                [0.0, cgb, -sgb],
                [-sga, cga*sgb, cga*cgb],
            ]

            depth = [1e9] * (W * H)
            rgb_buf = [(0, 0, 0)] * (W * H)

            for c in cubes:
                # 把整体旋转作用到立方体的位置与朝向上
                lpx, lpy, lpz = c['pos']
                px = G[0][0]*lpx + G[0][1]*lpy + G[0][2]*lpz
                py = G[1][0]*lpx + G[1][1]*lpy + G[1][2]*lpz
                pz = G[2][0]*lpx + G[2][1]*lpy + G[2][2]*lpz

                R = mat_mul(G, c['rot'])
                faces = c['faces']

                vx = px - cam_x; vy = py - cam_y; vz = pz - cam_z
                cz = vx*fx + vy*fy + vz*fz
                if cz < 0.4: continue
                cx = vx*rx + vy*ry + vz*rz
                cy = vx*ux + vy*uy + vz*uz

                sxc = cx / (cz * tan_h * aspect)
                syc = cy / (cz * tan_h)
                col_c = (sxc + 1.0) * W * 0.5
                row_c = (1.0 - syc) * H * 0.5

                rw = 0.87
                r_col = rw / (cz * tan_h * aspect) * W * 0.5
                r_row = rw / (cz * tan_h) * H * 0.5
                rad = (r_col if r_col > r_row else r_row) + 1.5

                c0 = int(col_c - rad); c1 = int(col_c + rad)
                r0 = int(row_c - rad); r1 = int(row_c + rad)
                if c0 < 0: c0 = 0
                if r0 < 0: r0 = 0
                if c1 > W - 1: c1 = W - 1
                if r1 > H - 1: r1 = H - 1
                if c0 > c1 or r0 > r1: continue

                r00, r01, r02 = R[0]
                r10, r11, r12 = R[1]
                r20, r21, r22 = R[2]
                t00, t01, t02 = r00, r10, r20
                t10, t11, t12 = r01, r11, r21
                t20, t21, t22 = r02, r12, r22

                ox = cam_x - px
                oy = cam_y - py
                oz = cam_z - pz
                o_lx = t00*ox + t01*oy + t02*oz
                o_ly = t10*ox + t11*oy + t12*oz
                o_lz = t20*ox + t21*oy + t22*oz

                h = CUBE_HALF

                for row in range(r0, r1 + 1):
                    base = row * W
                    for col in range(c0, c1 + 1):
                        idx = base + col
                        dx, dy, dz = ray_dirs[idx]
                        d_lx = t00*dx + t01*dy + t02*dz
                        d_ly = t10*dx + t11*dy + t12*dz
                        d_lz = t20*dx + t21*dy + t22*dz

                        tmin = -1e9; tmax = 1e9
                        h_axis = -1; h_sign = 0
                        valid = True

                        # X 轴板层
                        if -1e-9 < d_lx < 1e-9:
                            if o_lx < -h or o_lx > h: valid = False
                        else:
                            ta = (-h - o_lx) / d_lx
                            tb = ( h - o_lx) / d_lx
                            if ta > tb: ta, tb = tb, ta
                            if ta > tmin:
                                tmin = ta; h_axis = 0
                                h_sign = -1 if d_lx > 0 else 1
                            if tb < tmax: tmax = tb

                        # Y 轴板层
                        if valid:
                            if -1e-9 < d_ly < 1e-9:
                                if o_ly < -h or o_ly > h: valid = False
                            else:
                                ta = (-h - o_ly) / d_ly
                                tb = ( h - o_ly) / d_ly
                                if ta > tb: ta, tb = tb, ta
                                if ta > tmin:
                                    tmin = ta; h_axis = 1
                                    h_sign = -1 if d_ly > 0 else 1
                                if tb < tmax: tmax = tb

                        # Z 轴板层
                        if valid:
                            if -1e-9 < d_lz < 1e-9:
                                if o_lz < -h or o_lz > h: valid = False
                            else:
                                ta = (-h - o_lz) / d_lz
                                tb = ( h - o_lz) / d_lz
                                if ta > tb: ta, tb = tb, ta
                                if ta > tmin:
                                    tmin = ta; h_axis = 2
                                    h_sign = -1 if d_lz > 0 else 1
                                if tb < tmax: tmax = tb

                        if not valid: continue
                        if tmin > tmax or tmax < 0: continue
                        if tmin < 0 or tmin >= depth[idx]: continue
                        depth[idx] = tmin

                        if h_axis == 0:   nlx, nly, nlz = float(h_sign), 0.0, 0.0
                        elif h_axis == 1: nlx, nly, nlz = 0.0, float(h_sign), 0.0
                        else:             nlx, nly, nlz = 0.0, 0.0, float(h_sign)

                        nwx = r00*nlx + r01*nly + r02*nlz
                        nwy = r10*nlx + r11*nly + r12*nlz
                        nwz = r20*nlx + r21*nly + r22*nlz

                        diff = nwx*lx + nwy*ly + nwz*lz
                        if diff < 0: diff = 0
                        lum = 0.34 + 0.66 * diff

                        fi = h_axis * 2 + (0 if h_sign > 0 else 1)
                        base_col = faces[fi]

                        if base_col is None:
                            # 内部面：暗灰色，可以看清
                            cr = int(INNER_R * lum)
                            cg = int(INNER_G * lum)
                            cb = int(INNER_B * lum)
                        else:
                            br, bg, bb = base_col
                            cr = int(br * 255 * lum)
                            cg = int(bg * 255 * lum)
                            cb = int(bb * 255 * lum)
                            if cr > 255: cr = 255
                            if cg > 255: cg = 255
                            if cb > 255: cb = 255

                        rgb_buf[idx] = (cr, cg, cb)

            out = []
            for row in range(H):
                parts = []
                base = row * W
                for col in range(W):
                    idx = base + col
                    if depth[idx] > 1e8:
                        parts.append(' ')
                    else:
                        r_, g_, b_ = rgb_buf[idx]
                        parts.append('\033[38;2;%d;%d;%dm%s' % (r_, g_, b_, BLOCK))
                parts.append('\033[0m')
                out.append(''.join(parts))
            sys.stdout.write('\033[H' + '\n'.join(out))
            sys.stdout.flush()

            elapsed = time.time() - now
            if elapsed < 0.04:
                time.sleep(0.04 - elapsed)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
