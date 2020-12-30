# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Risk of deadly infection by age (for the unvaccinated).
# > Monthly risk of death due to COVID-19 infection for unvaccinated or not previosly infected. Mapped by country and age.
#
# - permalink: /micromorts-risk/
# - image: images/micromorts.png
# - author: <a href=https://github.com/artdgn/>artdgn</a>
# - categories: [world, overview, interactive, risk]
# - toc: false
# - hide: false

# > Important: This page contains estimations that were not calculated by an epidemiologist.

# +
#hide
import pandas as pd
try:  # using in REPL
    from . import covid_helpers
except ImportError:
    import covid_helpers

covid_data = covid_helpers.CovidData()
df_all, _, _ = covid_data.table_with_current_rates_and_ratios()
# -

#hide
df_all.columns.sort_values()

#hide_input
from IPython.display import Markdown
Markdown(f"*Based on data up to*: ***{covid_data.cur_date}***")

#hide
df_all['daily_infection_chance'] = (
    df_all['transmission_rate'] * df_all['current_active_ratio'] /
    (1 - df_all['current_active_ratio'] - df_all['current_recovered_ratio']))
df_all['monthly_infection_chance'] = 1 - (1 - df_all['daily_infection_chance']) ** 30
df_all['monthly_deadly_infection_risk'] = (
        df_all['monthly_infection_chance'] * df_all['age_adjusted_ifr'])
df_all['monthly_average_micromorts'] = df_all['monthly_deadly_infection_risk'] * 1e6
df_all['monthly_population_risk'] = df_all['monthly_deadly_infection_risk'] * df_all['population']

#hide
# errors
df_all['daily_infection_chance_err'] = (
    df_all['daily_infection_chance'] * df_all['transmission_rate_std'] /
    df_all['transmission_rate'])
df_all['monthly_infection_chance_err'] = (
    (1 - df_all['daily_infection_chance'] + df_all['daily_infection_chance_err']) ** 30 -
    (1 - df_all['daily_infection_chance'] - df_all['daily_infection_chance_err']) ** 30
) / 2
df_all['monthly_average_micromorts_err'] = (
    df_all['monthly_infection_chance_err'] * df_all['age_adjusted_ifr'] * 1e6)
df_all['monthly_population_risk_err'] = (
    df_all['monthly_population_risk'] * df_all['monthly_infection_chance_err'] /
    df_all['monthly_infection_chance'])

#hide
# retrospective empirical risk from recent deaths
df_all['daily_recent_empirical_risk'] = df_all['Deaths.new.per100k'] / 1e5
df_all['monthly_recent_empirical_risk'] = 1 - (1 - df_all['daily_recent_empirical_risk']) ** (30 / 5)
df_all['monthly_recent_empirical_micromorts'] = df_all['monthly_recent_empirical_risk'] * 1e6
df_all['monthly_population_empirical_risk'] = df_all['monthly_recent_empirical_risk'] * df_all['population']

#hide
# add age specific data
ifrs = covid_helpers.AgeAdjustedData.intl_ifrs
cols = covid_helpers.AgeAdjustedData.Cols
age_ifrs = {
    '0-29': ifrs.loc[cols.o4:cols.o29].mean(),
    '30-44': ifrs.loc[cols.o34:cols.o44].mean(),
    '45-59': ifrs.loc[cols.o49:cols.o59].mean(),
    '60-64': ifrs.loc[cols.o64],
    '65-69': ifrs.loc[cols.o69],
    '70-74': ifrs.loc[cols.o74],
    '75-79': ifrs.loc[cols.o79],
    '80+': ifrs.loc[cols.o84],
}
for age_range, ifr in age_ifrs.items():
    df_all[f'monthly_micromorts_{age_range}'] = 1e6 * ifr * df_all['monthly_infection_chance']
    df_all[f'monthly_micromorts_{age_range}_err'] = 1e6 * ifr * df_all['monthly_infection_chance_err']

#hide
geo_helper = covid_helpers.GeoMap
df_geo = geo_helper.make_geo_df(df_all, cases_filter=1000, deaths_filter=20)

# +
#hide
def micromorts_hover_func(r: pd.Series, age_range=None):    
    if age_range is None:
        ifr, ifr_str = r['age_adjusted_ifr'], "this country's age profile"
        micromorts_col='monthly_average_micromorts'
    else:
        ifr, ifr_str = age_ifrs[age_range], f'age range {age_range}'
        micromorts_col=f'monthly_micromorts_{age_range}'
    mm = r[micromorts_col]
    err = r[f'{micromorts_col}_err']
    return (
        f"<br>Risk of death due to one month<br>"
        f"of exposure is comparable to:<br>"
        f"  - <b>{mm * 10:.0f}</b> ± {err * 10:.0f} km by Motorcycle<br>"
        f"  - <b>{mm * 370:.0f}</b> ± {err * 370:.0f} km by Car<br>"
        f"  - <b>{mm * 1600:.0f}</b> ± {err * 1600:.0f} km by Plane<br>"  
        f"  - <b>{mm / 5:.0f}</b> ± {err / 5:.0f} scuba dives<br>"       
        f"  - <b>{mm / 8:.0f}</b> ± {err / 8:.0f} sky diving jumps<br>"         
        f"  - <b>{mm / 430:.0f}</b> ± {err / 430:.0f} base jumping jumps<br>"
        f"  - <b>{mm / 12000:.0f}</b> ± {err / 12000:.0f} Everest climbs<br><br>"      
        f"Contagious percent of population:"
        f"  <b>{r['current_active_ratio']:.1%}</b><br>"
        f"Susceptible percent of population:"
        f"  <b>{(1 - r['current_active_ratio'] - r['current_recovered_ratio']):.1%}</b><br>"
        f"Transmission rate: <b>{r['transmission_rate']:.1%}</b> ± {r['transmission_rate_std']:.1%}<br>"
        f"Chance of infection over a month:"
        f"  <b>{r['monthly_infection_chance']:.1%}</b> ± {r['monthly_infection_chance_err']:.1%}<br>"
        f"Chance of death after infection<br> (for {ifr_str}):"
        f"  <b>{ifr:.2%}</b>"
    )

def micromorts_hover_texts_for_age_range(age_range):
    return df_geo.apply(micromorts_hover_func, axis=1, age_range=age_range).tolist()

def stats_hover_text_func(r: pd.Series):
    return (
        "<br>"
        f"Cases (reported): {r['Cases.total']:,.0f} (+<b>{r['Cases.new']:,.0f}</b>)<br>"
        f"Cases (estimated): {r['Cases.total.est']:,.0f} (+<b>{r['Cases.new.est']:,.0f}</b>)<br>"
        f"Deaths: {r['Deaths.total']:,.0f} (+<b>{r['Deaths.new']:,.0f}</b>)<br><br>"
        f"Contagious percent of population:"
        f"  <b>{r['current_active_ratio']:.1%}</b><br>"
        f"Susceptible percent of population:"
        f"  <b>{(1 - r['current_active_ratio'] - r['current_recovered_ratio']):.1%}</b><br>"
        f"Transmission rate: <b>{r['transmission_rate']:.1%}</b> ± {r['transmission_rate_std']:.1%}<br>"
        f"Chance of infection over a month:"
        f"  <b>{r['monthly_infection_chance']:.1%}</b><br>"
    )


# -

#hide
import functools
default_age = '60-64'
colorscale = 'RdPu'
fig = geo_helper.make_map_figure(
    df_geo,
    col=f'monthly_micromorts_{default_age}',
    colorbar_title='Micromorts',
    subtitle=f"Ages {default_age}: risk of deadly infection due to a month's exposure",
    hover_text_func=functools.partial(micromorts_hover_func, age_range=default_age),
    scale_max=None,
    colorscale=colorscale,
    err_col=f'monthly_micromorts_{default_age}_err',
)

#hide
fig.update_layout(
    updatemenus=[
        dict(
            buttons=[
                geo_helper.button_dict(
                    df_geo[f'monthly_micromorts_{age_range}'],
                    title=f'<b>Ages {age_range} monthly risk in micromorts</b>',
                    colorbar_title='Micromorts',
                    colorscale=colorscale, scale_max=None, percent=False,
                    subtitle=f"Ages {age_range}: risk of deadly infection due to a month's exposure",
                    err_series=df_geo[f'monthly_micromorts_{age_range}_err'],
                    hover_text_list=micromorts_hover_texts_for_age_range(age_range)
                ) 
                for age_range in reversed(list(age_ifrs.keys()))
            ] + [
                geo_helper.button_dict(
                    df_geo['monthly_average_micromorts'],
                    title='<b>Average monthly risk in micromorts</b>',
                    colorbar_title='Micromorts',
                    colorscale=colorscale, scale_max=None, percent=False,
                    subtitle="Risk of deadly infection due to a month's exposure",
                    err_series=df_geo['monthly_average_micromorts_err'],
                    hover_text_list=micromorts_hover_texts_for_age_range(None)
                ),
                geo_helper.button_dict(
                    df_geo['monthly_infection_chance'],
                    title='<b>Monthly infection chance</b>',
                    colorbar_title='%',
                    colorscale='Reds', scale_max=None, percent=True,
                    subtitle="Chance of being infected during a month's exposure",
                    err_series=df_geo['monthly_infection_chance_err'],
                    hover_text_list=df_geo.apply(stats_hover_text_func, axis=1).tolist()
                ),
                geo_helper.button_dict(
                    df_geo['owid_vaccination_ratio'], '<b>Vaccination<br>percent</b>',
                    colorscale='Blues', scale_max=None, percent=True,
                    colorbar_title='%',
                    subtitle='Latest reported vaccination percent (OWID)'),
                geo_helper.button_dict(
                    df_geo['monthly_population_risk'],
                    title='<b>Montly total population risk</b>',
                    colorbar_title='Possible deaths',
                    colorscale='amp', scale_max=None, percent=False,
                    subtitle="Total possible deaths due to a month's exposure",
                    err_series=df_geo['monthly_population_risk_err'],
                    hover_text_list=df_geo.apply(stats_hover_text_func, axis=1).tolist()
                ),
                geo_helper.button_dict(
                    (df_geo['monthly_average_micromorts'] /
                     df_geo['monthly_recent_empirical_micromorts']),
                    title='<b>Ratio of average monthly risk<br>to recent deaths (as risk)</b>',
                    colorbar_title='%',
                    colorscale='Bluered', scale_max=200, percent=True,
                    subtitle="Ratio of average monthly risk to recent deaths expressed as risk",
                    err_series=None,
                    hover_text_list=df_geo.apply(stats_hover_text_func, axis=1).tolist()
                ),
            ],
            direction="down", bgcolor='#dceae1',
            pad={"t": 10},
            active=list(age_ifrs.keys())[::-1].index(default_age),
            showactive=True, x=0.1, xanchor="left", y=1.1, yanchor="top"),
    ]);

# ### Use dropdown menu to select specific age range
# > <font size=2>- Hover the mouse over a country for a risk comparison to some sports and travel modes.<br>- <a href="https://en.wikipedia.org/wiki/Micromort">"Micromorts"</a> are a measure of risk equal to 1 in a Million probability of death.<br>- Risk of death calculated for the unvaccinated or not previosly infected. </font>

#hide_input
# from IPython.display import HTML
# HTML(fig.to_html())
fig.show()

# > Tip: The map is zoomable and draggable. Double click to reset.

# ### Appendix: assumptions, explanations.
# <a id='appendix'></a>
# - Monthly risk calculation:
# $$
# Monthly\,Risk = Infection\,Fatality\,Rate_{age\,group} \cdot P_{montly\,infection}\\\,\\
# P_{montly\,infection} = 1 - (1 - P_{daily\,infection}) ^ {30\,days}\\\,\\
# P_{daily\,infection} = 
# \frac{Actively\,Infected\,\%\cdot Transmission\,Rate\,\%}
# {1 - Actively\,Infected\,\% - Recovered\,or\, Dead\,\%} \\
# $$
#   - "Actively Infected" and "Recovered or Dead" population percentages are estimated from past deaths and cases ([See estimations appendix in estimations & projections notebook](/covid-progress-projections/#appendix)).
#   - Age specific IFRs are taken from recent [Nature international meta-study of IFRs](https://www.nature.com/articles/s41586-020-2918-0#MOESM1).
#   - Country demographics for country average IFRs are taken from [UN demographic data for 2020](https://population.un.org/wpp/Download/Standard/Population/).
#   - Micromort deaths risk comparative data (travel and sports) are taken from [Wikipedia article on Micromorts](https://en.wikipedia.org/wiki/Micromort).
#   - The calculation is done on daily basis and extrapolated naively to a month.
# - **Why is everything "monthly"**? The main actionable question this analysis aims to help answer is **"How much risk is someone taking by not getting vaccinated now? What is the risk of waiting another month?"**. A daily timescale for this question is too short due to not being actionable, and on a scale much longer than a month the underlying data for calculations will change substantially (e.g. transmission rates, currently infected population) to not offer a reasonable appoximation. So a month felt to me as roughly the right time scale for the risk aggregation that is both easy to think about and should still be roughly correct.
# - Assumptions & limitations:
#     - The esposure is assumed to be **average exposure** typical of that country (as it manifests in the recent case and deaths data). Protective measures (e.g. masks) and self isolation should of course reduce the risk (if practiced more than the average for that population at that time).
#     - Susceptible population is assumed to not yet be **vaccinated**. When vaccination prevalence will become substantial, data will become available, and calculations can be adjusted. The risk estimates are for **regular susceptible** population. People who have been infected already are excluded (as recovered).
#     - All rates and percentages such as: transmission rate, active and recovered percentages are assumed to be **constant** during the month to keep the monthly calculation simple. This is of course NOT true. However although these rates do change, they usually change slowly enough for the likely result to still be of the same order of magnitude. It is possible to use values from a predictive model for this, but they too have errors (as they too are simplistic). For this analysis I preferred to go with the simple to calculate / understand approximation with a well understood error, than with the complex to calculate / understand approximation with an unknown error.
#     - All the additional assumptions from [estimations appendix in estimations & projections notebook](/covid-progress-projections/#appendix)
# - Vaccination effect on risk:
#     - The risk for the **vaccinated** is not calculated here. It is currently widely assumed that the reported [Moderna](https://en.wikipedia.org/wiki/MRNA-1273) and [Pfizer-BioNTech](https://en.wikipedia.org/wiki/Tozinameran) might reduce the **chance of infection** by around **90%**.
#     - While there are well founded estimates for the effect on **infection chance**, the effect on IFR (fatality rate) is much less known: how does vaccination affect the severity of the desease *if* infected? Answering this will require studying millions of vaccinated people, so will only be available later.
# - Additional related analyses:
#     - Another map of statistics of cases, deaths, ICU need and affected population percentage can be explored in [world-map part of the estimations & projections notebook](/covid-progress-projections/#World-map-(interactive))
#     - Per country predictive models of population ratios can be explored in [trajectories plots in estimations & projections notebook](/covid-progress-projections/#Interactive-plot-of-model-predictions-and-past-data)
# ![](https://artdgn.goatcounter.com/count?p=c19d-morts)
