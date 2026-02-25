# -*- coding: utf-8 -*-
"""Source parameter inversion and initial ratios."""
import numpy as np

from .engine import engine


def calculate_mu_sk(Pb206_204_S, Pb207_204_S, t_Ma, params=None):
    """
    计算源区 Mu 值 (238U/204Pb)
    
    说明:
    此函数基于给定的样品年龄 t 和测量比值，反演产生该铅同位素组成的源区 U/Pb 比。
    计算假设铅从初始时间 T (T2) 以单一阶段演化到 t (近似)。
    
    Returns:
        np.ndarray: 源区 Mu 值
    """
    if params is None: params = engine.params
    
    l238 = params['lambda_238']
    l235 = params['lambda_235']
    T = params['T2']
    a_init = params['a0']
    b_init = params['b0']
    u_ratio = params['U_ratio']

    # 数据预处理
    Pb206 = np.asarray(Pb206_204_S)
    Pb207 = np.asarray(Pb207_204_S)
    
    # 年龄预处理
    if t_Ma is None:
        t = np.array(np.nan)
    else:
        try:
            t = np.asarray(t_Ma, dtype=float)
        except (ValueError, TypeError):
             # 处理可能包含 None 的对象数组
             t_arr = np.asarray(t_Ma)
             if t_arr.ndim == 0:
                 t = np.array(np.nan)
             else:
                 t_flat = []
                 for x in t_arr.ravel():
                     try: t_flat.append(float(x)) 
                     except: t_flat.append(np.nan)
                 t = np.array(t_flat).reshape(t_arr.shape)

    t = np.maximum(t, 0) * 1e6
    
    # 1. 计算等时线斜率 slope
    num = np.exp(l235 * t) - 1
    den = np.exp(l238 * t) - 1
    den = np.where(np.abs(den) < 1e-50, 1e-50, den)
    slope_t = num / ((1.0 / u_ratio) * den)
    
    # 2. 计算放射性成因增量因子
    rad207_growth = u_ratio * (np.exp(l235 * T) - np.exp(l235 * t))
    rad206_growth = np.exp(l238 * T) - np.exp(l238 * t)
    
    # 3. 求解 Mu
    numerator = (Pb207 - b_init) - slope_t * (Pb206 - a_init)
    denominator = rad207_growth - slope_t * rad206_growth
    denominator = np.where(np.abs(denominator) < 1e-50, 1e-50, denominator)
    
    return numerator / denominator

def calculate_omega_sk(Pb208_204_S, t_Ma, params=None):
    """
    计算源区 Omega 值 (232Th/204Pb)
    
    基于 208Pb 生长方程: Pb208 = c0 + omega * (e^λ2*T - e^λ2*t)
    """
    if params is None: params = engine.params
    l232 = params['lambda_232']
    T = params['T2']
    c_init = params['c0']
    
    Pb208 = np.asarray(Pb208_204_S)
    
    if t_Ma is None:
        t = np.array(np.nan)
    else:
        try:
             t = np.asarray(t_Ma, dtype=float)
        except:
             # 简化处理异常
             t = np.full_like(Pb208, np.nan)

    t = np.maximum(t, 0) * 1e6
    
    denom = np.exp(l232 * T) - np.exp(l232 * t)
    denom = np.where(np.abs(denom) < 1e-50, 1e-50, denom)
    
    return (Pb208 - c_init) / denom

def calculate_nu_sk(mu, params=None):
    """
    计算源区 Nu 值 (235U/204Pb)
    nu = mu * (235U/238U)
    """
    if params is None: params = engine.params
    u_ratio = params['U_ratio']
    return mu * u_ratio

def calculate_mu_sk_model(Pb206_204_S, Pb207_204_S, t_Ma, params=None):
    """
    计算模型源区 Mu (对应 R 包 PbIso 中的 CalcMu)
    此函数严格遵循 Stacey & Kramers (1975) 第二阶段模型参数。
    
    Args:
        Pb206_204_S, Pb207_204_S: 样品同位素比值
        t_Ma: 样品年龄 (Ma)
        
    Returns:
        np.ndarray: 源区 Mu 值, 表示从 Tsec (3.7Ga) 到 t 阶段的 238U/204Pb 比值。
    """
    if params is None: params = engine.params
    
    l5 = params['lambda_235']
    l8 = params['lambda_238']
    
    T1 = params['T1'] 
    X1 = params['a1']
    Y1 = params['b1']
    u_ratio = params['U_ratio']
    U8U5 = 1.0 / u_ratio if u_ratio != 0 else 137.88
    
    t = np.asarray(t_Ma) * 1e6
    x = np.asarray(Pb206_204_S)
    y = np.asarray(Pb207_204_S)
    
    # 核心算法 (源自 PbIso CalcMu)
    e5t = np.exp(l5 * t)
    e8t = np.exp(l8 * t)
    e5T = np.exp(l5 * T1)
    e8T = np.exp(l8 * T1)
    
    term_slope = (e5t - 1) / (U8U5 * (e8t - 1))
    
    num = term_slope * (X1 - x) + y - Y1
    den = (e5T - e5t) / U8U5 - term_slope * (e8T - e8t)
    den = np.where(np.abs(den) < 1e-50, 1e-50, den)
    
    return num / den

def calculate_kappa_sk_model(Pb208_204_S, Pb206_204_S, t_Ma, params=None):
    """
    计算模型源区 kappa (Th/U) (对应 R 包 PbIso 中的 CalcKa)
    
    Returns:
        np.ndarray: 源区 Kappa 值 (232Th/238U)
    """
    if params is None: params = engine.params
    
    l238 = params['lambda_238']
    l232 = params['lambda_232']
    
    T = params['T1']
    X1 = params['a1']
    Z1 = params['c1']
    
    t = np.asarray(t_Ma) * 1e6
    x = np.asarray(Pb206_204_S)
    z = np.asarray(Pb208_204_S)
    
    num_time = np.exp(l238 * T) - np.exp(l238 * t)
    den_time = np.exp(l232 * T) - np.exp(l232 * t)
    den_time = np.where(np.abs(den_time) < 1e-50, 1e-50, den_time)
    
    dx = x - X1
    dx = np.where(np.abs(dx) < 1e-50, 1e-50, dx)
    
    kappa = ((z - Z1) / dx) * (num_time / den_time)
    
    return kappa

def calculate_initial_ratio_64(t_Ma, Pb206_204_S, Pb207_204_S, params=None):
    """
    计算样品形成时的初始 206Pb/204Pb (对应 PbIso Calc64in)
    """
    if params is None: params = engine.params
    
    l5 = params['lambda_235']
    l8 = params['lambda_238']
    T1 = params['T1']
    X1 = params['a1']
    Y1 = params['b1']
    u_ratio = params['U_ratio']
    U8U5 = 1.0 / u_ratio
    
    t = np.asarray(t_Ma) * 1e6
    x = np.asarray(Pb206_204_S)
    y = np.asarray(Pb207_204_S)

    # 1. 计算 Mu
    e5t = np.exp(l5 * t)
    e8t = np.exp(l8 * t)
    e5T = np.exp(l5 * T1)
    e8T = np.exp(l8 * T1)
    
    term_slope = (e5t - 1) / (U8U5 * (e8t - 1))
    mu_num = term_slope * (X1 - x) + y - Y1
    mu_den = (e5T - e5t) / U8U5 - term_slope * (e8T - e8t)
    mu_den = np.where(np.abs(mu_den) < 1e-50, 1e-50, mu_den)
    mu = mu_num / mu_den
    
    # 2. 计算初始比值: X_init = X1 + mu * (e^λ8*T1 - e^λ8*t)
    # 实际上这是计算模型在时间 t 的值
    res = X1 + mu * (e8T - e8t)
    return res

def calculate_initial_ratio_74(t_Ma, Pb206_204_S, Pb207_204_S, params=None):
    """
    计算样品形成时的初始 207Pb/204Pb (对应 PbIso Calc74in)
    """
    if params is None: params = engine.params
    
    l5 = params['lambda_235']
    l8 = params['lambda_238']
    T1 = params['T1']
    X1 = params['a1']
    Y1 = params['b1']
    u_ratio = params['U_ratio']
    U8U5 = 1.0 / u_ratio
    
    t = np.asarray(t_Ma) * 1e6
    x = np.asarray(Pb206_204_S)
    y = np.asarray(Pb207_204_S)
    
    # 1. 计算 Mu
    e5t = np.exp(l5 * t)
    e8t = np.exp(l8 * t)
    e5T = np.exp(l5 * T1)
    e8T = np.exp(l8 * T1)
    
    term_slope = (e5t - 1) / (U8U5 * (e8t - 1))
    mu_num = term_slope * (X1 - x) + y - Y1
    mu_den = (e5T - e5t) / U8U5 - term_slope * (e8T - e8t)
    mu_den = np.where(np.abs(mu_den) < 1e-50, 1e-50, mu_den)
    mu = mu_num / mu_den
    
    # 2. 计算初始比值: Y_init = Y1 + (mu/U_ratio) * (e^λ5*T1 - e^λ5*t)
    res = Y1 + (mu / U8U5) * (e5T - e5t)
    return res

def calculate_initial_ratio_84(t_Ma, Pb206_204_S, Pb207_204_S, Pb208_204_S, params=None):
    """
    计算样品形成时的初始 208Pb/204Pb (对应 PbIso Calc84in)
    """
    if params is None: params = engine.params
    
    l5 = params['lambda_235']
    l8 = params['lambda_238']
    l2 = params['lambda_232']
    T1 = params['T1']
    X1 = params['a1']
    Y1 = params['b1']
    Z1 = params['c1']
    u_ratio = params['U_ratio']
    U8U5 = 1.0 / u_ratio
    
    t = np.asarray(t_Ma) * 1e6
    x = np.asarray(Pb206_204_S)
    y = np.asarray(Pb207_204_S)
    z = np.asarray(Pb208_204_S)
    
    e5t = np.exp(l5 * t)
    e8t = np.exp(l8 * t)
    e2t = np.exp(l2 * t)
    e5T = np.exp(l5 * T1)
    e8T = np.exp(l8 * T1)
    e2T = np.exp(l2 * T1)
    
    # 1. 计算 Mu
    term_slope = (e5t - 1) / (U8U5 * (e8t - 1))
    mu_num = term_slope * (X1 - x) + y - Y1
    mu_den = (e5T - e5t) / U8U5 - term_slope * (e8T - e8t)
    mu_den = np.where(np.abs(mu_den) < 1e-50, 1e-50, mu_den)
    mu = mu_num / mu_den
    
    # 2. 计算 Kappa
    den_k_num = e2T - e2t
    den_k_den = e8T - e8t
    den_k_den = np.where(np.abs(den_k_den) < 1e-50, 1e-50, den_k_den)
    kappa = ((z - Z1) / (x - X1)) / (den_k_num / den_k_den)
    
    # 3. 计算 Omega 并得出初始 208
    omega = kappa * mu
    res = Z1 + omega * (e2T - e2t)
    
    return res
