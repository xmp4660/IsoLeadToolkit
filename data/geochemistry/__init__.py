# -*- coding: utf-8 -*-
"""Geochemistry package exports."""
import numpy as np

from .engine import (
    PRESET_MODELS,
    GeochemistryEngine,
    engine,
    calculate_modelcurve,
    _exp_evolution_term,
    T_EARTH_1ST,
    T_EARTH_CANON,
    T_SK_STAGE2,
    LAMBDA_238,
    LAMBDA_235,
    LAMBDA_232,
    A0,
    B0,
    C0,
    A1_SK,
    B1_SK,
    C1_SK,
    MU_M_DEFAULT,
    OMEGA_M_DEFAULT,
    U_RATIO_NATURAL,
    REGRESSION_A,
    REGRESSION_B,
    REGRESSION_C,
    E1_DEFAULT,
    E2_DEFAULT,
)
from .age import (
    calculate_single_stage_age,
    calculate_two_stage_age,
    calculate_model_age,
)
from .source import (
    calculate_mu_sk,
    calculate_omega_sk,
    calculate_nu_sk,
    calculate_mu_sk_model,
    calculate_kappa_sk_model,
    calculate_initial_ratio_64,
    calculate_initial_ratio_74,
    calculate_initial_ratio_84,
)
from .delta import (
    calculate_deltas,
    calculate_v1v2_coordinates,
    calculate_delta_values,
    calculate_v1v2,
)
from .isochron import (
    calculate_paleoisochron_line,
    calculate_isochron1_growth_curve,
    calculate_isochron2_growth_curve,
    york_regression,
    calculate_pbpb_age_from_ratio,
    calculate_isochron_age_from_slope,
    calculate_source_mu_from_isochron,
    calculate_source_kappa_from_slope,
)


def calculate_all_parameters(Pb206_204_S, Pb207_204_S, Pb208_204_S, calculate_ages=True, a=None, b=None, c=None, scale=1.0, t_Ma=None, **kwargs):
    """
    计算所有地球化学参数 (主调用接口)
    
    集成功能:
    1. 计算单阶段(CDT)和两阶段(SK)模式年龄
    2. 计算 Delta 值和 V1-V2 坐标
    3. 计算源区特征 (Mu, Omega, Kappa)
    4. 计算初始同位素比值
    
    Args:
        Pb206_204_S, ...: 同位素比值数据
        a, b, c: 可选的 V1V2 回归参数覆盖
        t_Ma: 样品真实年龄 (Ma)，用于 CalcMu/CalcKa/Calc*in（若未提供则使用 tSK）
        
    Returns:
        dict: 包含所有计算结果的字典
    """
    # 1. 数据标准化
    Pb206 = np.asarray(Pb206_204_S)
    Pb207 = np.asarray(Pb207_204_S)
    Pb208 = np.asarray(Pb208_204_S)
    
    results = {
        'Pb206_204_S': Pb206,
        'Pb207_204_S': Pb207,
        'Pb208_204_S': Pb208,
    }
    
    # 获取当前模型设置
    current_model = getattr(engine, 'current_model_name', '')
    # V1V2 (Geokit) 模式特殊处理: 使用 T1=4.43Ga 计算 tCDT
    is_geokit = "Geokit" in current_model
    # 仅在明确的两阶段模型中使用两阶段逻辑
    is_two_stage = "2nd Stage" in current_model or current_model.endswith("(2nd Stage)")
    
    # 2. 模式年龄计算
    params_calc = engine.get_parameters()
    if is_geokit:
        tCDT = calculate_single_stage_age(Pb206, Pb207, initial_age=engine.params['T1'])
    else:
        tCDT = calculate_single_stage_age(Pb206, Pb207)

    tSK = calculate_two_stage_age(Pb206, Pb207)

    if t_Ma is None:
        t_input = tSK
    else:
        t_input = np.asarray(t_Ma, dtype=float)
        if t_input.ndim == 0:
            if not np.isfinite(t_input):
                t_input = tSK
        else:
            t_input = np.where(np.isfinite(t_input), t_input, tSK)
    
    results['tCDT (Ma)'] = tCDT
    results['tSK (Ma)'] = tSK
    
    # 3. Delta 值计算
    E1_val = kwargs.get('E1', None)
    E2_val = kwargs.get('E2', None)

    if is_two_stage:
        t_model = tSK
        d_alpha, d_beta, d_gamma = calculate_deltas(
            Pb206, Pb207, Pb208, t_model, params=params_calc, use_two_stage=True, E1=E1_val, E2=E2_val
        )
    else:
        # 默认 V1V2 逻辑: 使用 T1=4.43Ga 计算出的单阶段年龄作为基准
        t_calc = tCDT if is_geokit else calculate_single_stage_age(Pb206, Pb207, params=params_calc, initial_age=params_calc.get('T2'))
        if params_calc.get('v1v2_formula') == 'zhu1993':
            t_calc = np.maximum(t_calc, 0)
        d_alpha, d_beta, d_gamma = calculate_deltas(
            Pb206, Pb207, Pb208, t_calc, params=params_calc, use_two_stage=False, E1=E1_val, E2=E2_val
        )
        
    results.update({
        'Delta_alpha': d_alpha,
        'Delta_beta': d_beta,
        'Delta_gamma': d_gamma
    })
    
    # 4. V1-V2 坐标计算
    params_temp = params_calc.copy()
    if a is not None: params_temp['a'] = a
    if b is not None: params_temp['b'] = b
    if c is not None: params_temp['c'] = c
    
    v1, v2 = calculate_v1v2_coordinates(d_alpha, d_beta, d_gamma, params=params_temp)
    results['V1'] = v1
    results['V2'] = v2
    
    # 5. 源区参数反演
    # 使用真实年龄（若提供），否则回退到 tSK
    mu_val = calculate_mu_sk(Pb206, Pb207, t_input, params=params_calc)
    results['mu'] = mu_val
    results['nu'] = calculate_nu_sk(mu_val, params=params_calc)
    results['omega'] = calculate_omega_sk(Pb208, t_input, params=params_calc)
    
    # 5.2 R语言 PbIso 对应参数 (严格 SK 模型)
    mu_sk = calculate_mu_sk_model(Pb206, Pb207, t_input, params=params_calc)
    kappa_sk = calculate_kappa_sk_model(Pb208, Pb206, t_input, params=params_calc)
    results['mu_SK'] = mu_sk
    results['kappa_SK'] = kappa_sk
    results['omega_SK'] = kappa_sk * mu_sk # Omega = Kappa * Mu
    
    # 6. 初始比值反演 (基于真实年龄或 tSK)
    results['Init_206_204'] = calculate_initial_ratio_64(t_input, Pb206, Pb207, params=params_calc)
    results['Init_207_204'] = calculate_initial_ratio_74(t_input, Pb206, Pb207, params=params_calc)
    results['Init_208_204'] = calculate_initial_ratio_84(t_input, Pb206, Pb207, Pb208, params=params_calc)
    
    return results

__all__ = [
    'T_EARTH_1ST',
    'T_EARTH_CANON',
    'T_SK_STAGE2',
    'LAMBDA_238',
    'LAMBDA_235',
    'LAMBDA_232',
    'A0',
    'B0',
    'C0',
    'A1_SK',
    'B1_SK',
    'C1_SK',
    'MU_M_DEFAULT',
    'OMEGA_M_DEFAULT',
    'U_RATIO_NATURAL',
    'REGRESSION_A',
    'REGRESSION_B',
    'REGRESSION_C',
    'E1_DEFAULT',
    'E2_DEFAULT',
    'PRESET_MODELS',
    'GeochemistryEngine',
    'engine',
    'calculate_modelcurve',
    'calculate_single_stage_age',
    'calculate_two_stage_age',
    'calculate_model_age',
    'calculate_mu_sk',
    'calculate_omega_sk',
    'calculate_nu_sk',
    'calculate_mu_sk_model',
    'calculate_kappa_sk_model',
    'calculate_initial_ratio_64',
    'calculate_initial_ratio_74',
    'calculate_initial_ratio_84',
    'calculate_deltas',
    'calculate_v1v2_coordinates',
    'calculate_delta_values',
    'calculate_v1v2',
    'calculate_paleoisochron_line',
    'calculate_isochron1_growth_curve',
    'calculate_isochron2_growth_curve',
    'york_regression',
    'calculate_pbpb_age_from_ratio',
    'calculate_isochron_age_from_slope',
    'calculate_source_mu_from_isochron',
    'calculate_source_kappa_from_slope',
    'calculate_all_parameters',
]
