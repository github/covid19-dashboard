# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + [markdown] papermill={"duration": 0.013695, "end_time": "2020-03-27T06:31:15.895652", "exception": false, "start_time": "2020-03-27T06:31:15.881957", "status": "completed"} tags=[]
# # Progress projections, immunity, ICU demand for COVID 19.
# > Estimating and projecting current and future percentage immunity per country, current and future need for ICUs beds, total cases from deaths, and cases and deaths per 100k.
#
# - comments: true
# - categories: [overview]
# - author: artdgn
# - image: images/covid-progress-projections.png
# - permalink: /covid-progress-projections/
# - hide: false
# -

# ## What is this about:
# 1. **How long will it take until substantial percentages of immunity (to start resuming normal life)?**
#
#   *Assuming recovery implies immunity, assuming current infection rates, assuming no globally available vaccine or treatment in near future.*
#
# 2. **How bad is the impending medical crisis in different countries?**
#
#   *Assuming that the bottleneck is the need for ICU beds, and assuming current infection rates.*
#   
# #### Assumption of current infection rates is not to say that they won't be reduced, but to understand the implications of not reducing them. 

# + papermill={"duration": 0.330834, "end_time": "2020-03-27T06:31:16.261108", "exception": false, "start_time": "2020-03-27T06:31:15.930274", "status": "completed"} tags=[]
#hide
import pandas as pd
import overview_helpers

helper = overview_helpers.OverviewDataExtras
df = helper.filter_df(helper.table_with_projections())
df.columns
# -

# ## Top 20 by estimated immunisation progress: 
# - "*Immune*" here means "not susceptible" from [SIR model](https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology#The_SIR_model): previously infected (recovered / dead / actively ill). This assumes that recovery means immunity (details at the bottom). 
# - Estimation for current case numbers is done from deaths (details at the bottom).
# - Growth rate is estimated from last 5 days data by weighted average of daily case growth rates.
# - Sorted by number of estimated new cases.
#

#hide_input
rename_cols = {'immune_ratio.est': 'Estimated <br> Immune currently', 
               'immune_ratio.est.+14d': 'Projected <br> In 14 days', 
               'immune_ratio.est.+30d': 'Projected <br> In 30 days',
               'immune_ratio.est.+60d': 'Projected <br> In 60 days',
               'Fatality Rate': 'Reported <br> fatality <br> percentage',
               'growth_rate': 'Estimated <br> case growth <br> daily rate',
              }
progress_cols = list(rename_cols.values())[:4]
df_progress_bars = df.rename(rename_cols, axis=1)
df_progress_bars.sort_values('Cases.new.est', ascending=False)\
[rename_cols.values()]\
.head(20).style\
    .bar(subset=progress_cols[0], color='#279931', vmin=0, vmax=1.0)\
    .bar(subset=progress_cols[1], color='#5dad64', vmin=0, vmax=1.0)\
    .bar(subset=progress_cols[2], color='#719974', vmin=0, vmax=1.0)\
    .bar(subset=progress_cols[3], color='#a1afa3', vmin=0, vmax=1.0)\
    .bar(subset=[rename_cols['Fatality Rate']], color='#420412', vmin=0, vmax=0.1)\
    .applymap(lambda _: 'color: red', subset=[rename_cols['Fatality Rate']])\
    .bar(subset=[rename_cols['growth_rate']], color='#d65f5f', vmin=0, vmax=1)\
    .set_precision(2).format('<b>{:.1%}</b>', subset=list(rename_cols.values()))


# ## Top 20 by estimated need for ICU beds:
# - ICU need is estimated as 6% of active cases.
# - Actively sick ratios are taken from the SIR model (which is initialised with case numbers estimated from reported deaths, and estimated growth rate from last 5 days).

#hide_input
rename_cols = {'needICU.per100k': 'Estimated <br> Current need <br> per 100k', 
               'needICU.per100k.+14d': 'Projected <br> In 14 days', 
               'needICU.per100k.+30d': 'Projected <br> In 30 days',
               'needICU.per100k.+60d': 'Projected <br> In 60 days',
               'Deaths.new.per100k': 'New deaths <br> per 100k <br> in 5 days',
               'growth_rate': 'Estimated <br> case growth <br> daily rate',
              }
icu_cols = list(rename_cols.values())[:4]
df_icu_bars = df.rename(rename_cols, axis=1)
df_icu_bars.sort_values(rename_cols['needICU.per100k'], ascending=False)\
[rename_cols.values()]\
.head(20).style\
    .bar(subset=icu_cols[0], color='#f43d64', vmin=0, vmax=10)\
    .bar(subset=icu_cols[1], color='#ef8ba0', vmin=0, vmax=10)\
    .bar(subset=icu_cols[2], color='#e597a8', vmin=0, vmax=10)\
    .bar(subset=icu_cols[3], color='#e0c5cb', vmin=0, vmax=10)\
    .bar(subset=[rename_cols['Deaths.new.per100k']], color='#340849', vmin=0, vmax=10)\
    .applymap(lambda _: 'color: red', subset=[rename_cols['Deaths.new.per100k']])\
    .bar(subset=[rename_cols['growth_rate']], color='#d65f5f', vmin=0, vmax=1)\
    .format('<b>{:.1%}</b>', subset=[rename_cols['growth_rate']])\
    .format('<b>{:.2}</b>', subset=[rename_cols['Deaths.new.per100k']])\
    .format('<b>{:.2f}</b>', subset=icu_cols)\
    .set_precision(2)

# ## Full table with more details:
#  - Contains reported data, estimations, projections, and numbers relative to population.
#  - This is a busy table in order to present as many stats as possible for each country for people to be able to inspect their counties of interest in maximum amount detail (without running the notebook).
#  - Sorted by projected need for ICU beds per 100k in 14 days. 
#  - **New** in this table means **during last 5 days**.
#  - Includes only countries with at least 10 deaths.

# +
#hide_input
pretty_cols = {}

pretty_cols['deaths'] = 'Deaths <br> - Reported (+new) <br> - Per100k (+new) '
df[pretty_cols['deaths']] =(df.apply(lambda r: f" \
                         {r['Deaths.total']:,.0f} \
                         (+<b>{r['Deaths.new']:,.0f}</b>) <br> \
                         Per 100k: {r['Deaths.total.per100k']:,.1f} \
                         (+<b>{r['Deaths.new.per100k']:,.1f}</b>) \
                         ", axis=1))

pretty_cols['cases'] = 'Cases <br> - Reported (+new) <br> - Estimated (+new) '
df[pretty_cols['cases']] =(df.apply(lambda r: f" \
                         {r['Cases.total']:,.0f} \
                         (+<b>{r['Cases.new']:,.0f}</b>) <br>\
                         Est: {r['Cases.total.est']:,.0f} \
                         (+<b>{r['Cases.new.est']:,.0f}</b>)\
                         ", axis=1))

pretty_cols['icu'] = ('Estimated <br> Need for ICU <br> per 100k <br>\
                      - Current <br> - (in 14/30/60 days)')
df[pretty_cols['icu']] =(df.apply(lambda r: f"\
                        <b>{r['needICU.per100k']:.2f}</b> <br>\
                        ({r['needICU.per100k.+14d']:.1f} / \
                        {r['needICU.per100k.+30d']:.1f} / \
                        {r['needICU.per100k.+60d']:.1f}) \
                        ", axis=1))

pretty_cols['progress'] = ('Immunized <br> percentage <br> \
                      - Reported (Estimated) <br> - (in 14/30/60 days)')
df[pretty_cols['progress']] =(df.apply(lambda r: f" \
                        {r['immune_ratio']:.2%} \
                        <b>({r['immune_ratio.est']:.2%})</b> <br>\
                        ({r['immune_ratio.est.+14d']:.1%} / \
                        {r['immune_ratio.est.+30d']:.1%} / \
                        {r['immune_ratio.est.+60d']:.1%})", axis=1))

df.sort_values('needICU.per100k.+14d', ascending=False)\
    [pretty_cols.values()]\
    .style.set_na_rep("-").set_properties(**{})
# -

# ### Assumptions and references:
# - I'm not an epidemiologist. This is an attempt to understand what's happening, and what the future looks like if current trends remain unchanged.
# - Everything is approximated and depends heavily on underlying assumptions.
# - Immunisation:
#     - "*Immune*" and "*Immunisation*" here means "not susceptible" from [SIR model](https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology#The_SIR_model): previously infected (recovered / dead / actively ill). 
#     - This also assumes that recovery means immunity from the virus. This is a reasonable assumption (for a particular strain) because at least currently the patient's immune system is the main mechanism by which the infection is removed.
#     - This will not hold true if there are multiple strains for which immunity needs to be developed independently (like in the case of flu or the common cold).    
# - Total case estimation is done from deaths by:
#     - Assuming that unbiased fatality rate is 1.5% (from heavily tested countries / the cruise ship data) and that it takes 8 days on average for a case to go from being confirmed positive (after incubation + testing lag) to death. This is the same figure used by ["Estimating The Infected Population From Deaths"](https://covid19dashboards.com/covid-infected/) in this repo.
#     - The estimated testing bias then multiplies the reported case numbers to estimate the *true* case numbers (*=case numbers if everyone was tested*).
#     - The testing bias calculation is probably the highest source of uncertainty in all these estimations and projections. Better source of testing bias (or just *true case* numbers), should make everything more accurate.
# - Projection is done using a simple [SIR model](https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology#The_SIR_model) with (examples below):
#     - Growth rate calculated over the 5 past days. This is pessimistic - because it includes the testing rate growth rate as well, and is slow to react to both improvements in test coverage and "flattening".
#     - Recovery probability being 1/20 (for 20 days to recover).
# - ICU need is calculated as being [6% of active cases](https://medium.com/@joschabach/flattening-the-curve-is-a-deadly-delusion-eea324fe9727) where:
#     - Active cases are taken from the SIR model.
#     - This is both pessimistic - because real ICU rate may in reality be lower, due to testing biases, and especially in "younger" populations), and optimistic - because active cases which are on ICU take longer (so need the ICUs for longer).
#     - [Some numbers](https://www.forbes.com/sites/niallmccarthy/2020/03/12/the-countries-with-the-most-critical-care-beds-per-capita-infographic/) on actual capacity of ICUs per 100k (didn't find a full dataset for a lot of countries yet).

# ### Examples of SIR model plots:
# - The purpose is to demonstrate the calculations.
# - For countries that ranked highest in:
#   - Estimated new cases.
#   - Projected need for ICU in 14 days.
#   - Projected immunisation percentage in 14 days.

#hide_input
sir_plot_countries = df[['needICU.per100k.+14d', 
                         'Cases.new.est', 
                         'immune_ratio.est.+14d']].idxmax().unique()
for c in sir_plot_countries:
    helper.table_with_projections(debug_country=c)
