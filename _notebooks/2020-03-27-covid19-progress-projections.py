# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
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
# # Progress projection, immunity, ICU demand for COVID 19.
# > Estimating and projecting - current and future percentage immunity per country, current and future need for ICUs beds, total cases from deaths, and cases and deaths per 100k.
#
# - comments: true
# - categories: [overview]
# - author: artdgn
# - image: images/covid-progress-projections.png
# - permalink: /covid-progress-projections/
# - hide: false

# + papermill={"duration": 0.330834, "end_time": "2020-03-27T06:31:16.261108", "exception": false, "start_time": "2020-03-27T06:31:15.930274", "status": "completed"} tags=[]
#hide
import pandas as pd
import overview_helpers

helper = overview_helpers.OverviewDataExtras
df = helper.filter_df(helper.table_with_projections())
df.columns
# -

# ## Top 20 by immunisation progress: 
# - With current reported fatality rate and current case growth rate.
# - Sorted by number of new cases (estimated).
#

#hide_input
rename_cols = {'immune_ratio': 'Immune currently', 
               'immune_ratio.+14d': 'In 14 days', 
               'immune_ratio.+30d': 'In 30 days',
               'immune_ratio.+60d': 'In 60 days',
               'Fatality Rate': 'Reported <br> fatality rate',
               'growth_rate': 'Case growth <br> rate',
              }
progress_cols = list(rename_cols.values())[:4]
df_progress_bars = df.rename(rename_cols, axis=1)
df_progress_bars.sort_values('Cases.new.est', ascending=False)\
[rename_cols.values()]\
.head(20)\
    .style.bar(subset=progress_cols, color='#5fba7d', vmin=0, vmax=1.0)\
    .bar(subset=[rename_cols['Fatality Rate']], color='#420412', vmin=0, vmax=10)\
    .applymap(lambda _: 'color: red', subset=[rename_cols['Fatality Rate']])\
    .bar(subset=[rename_cols['growth_rate']], color='#d65f5f', vmin=1, vmax=2)\
    .set_precision(2).format('{:.1%}', subset=progress_cols)


# ## Top 20 by need for ICU beds per 100k with projections:
# - With current new deaths burden (per 100k) and current case growth rate.

#hide_input
rename_cols = {'needICU.per100k': 'Current need <br> per 100k', 
               'needICU.per100k.+14d': 'In 14 days', 
               'needICU.per100k.+30d': 'In 30 days',
               'needICU.per100k.+60d': 'In 60 days',
               'Deaths.new.per100k': 'New deaths <br> per 100k',
               'growth_rate': 'Case growth <br> rate',
              }
icu_cols = list(rename_cols.values())[:4]
df_icu_bars = df.rename(rename_cols, axis=1)
df_icu_bars.sort_values(rename_cols['needICU.per100k'], ascending=False)\
[rename_cols.values()]\
.head(20)\
    .style.bar(subset=icu_cols, color='#f43d64', vmin=0, vmax=10)\
    .bar(subset=[rename_cols['Deaths.new.per100k']], color='#340849', vmin=0, vmax=10)\
    .applymap(lambda _: 'color: red', subset=[rename_cols['Deaths.new.per100k']])\
    .bar(subset=[rename_cols['growth_rate']], color='#d65f5f', vmin=1, vmax=2)\
    .set_precision(2).format('{:.2f}', subset=icu_cols)

# ## Full overview and Need for ICU beds per 100K population, current and projected:
#  - Sorted by current (estimated) need.
#  - Only for countries with at least 10 deaths.

# +
#hide_input
pretty_cols = {}

pretty_cols['deaths'] = 'Deaths (+new)'
df[pretty_cols['deaths']] =(df.apply(lambda r: f" \
                         {r['Deaths.total']:,.0f} \
                         (+<b>{r['Deaths.new']:,.0f}</b>) <br> \
                         Per 100k: {r['Deaths.total.per100k']:,.1f} \
                         (+<b>{r['Deaths.new.per100k']:,.1f}</b>) \
                         ", axis=1))

pretty_cols['cases'] = 'Cases (+new)'
df[pretty_cols['cases']] =(df.apply(lambda r: f" \
                         {r['Cases.total']:,.0f} \
                         (+<b>{r['Cases.new']:,.0f}</b>) <br>\
                         Est: {r['Cases.total.est']:,.0f} \
                         (+<b>{r['Cases.new.est']:,.0f}</b>)\
                         ", axis=1))

pretty_cols['icu'] = 'Need ICU <br>per 100k <br> (+ in 14/30/60 days)'
df[pretty_cols['icu']] =(df.apply(lambda r: f"\
                        <b>{r['needICU.per100k']:.2f}</b> <br>\
                        ({r['needICU.per100k.+14d']:.1f} / \
                        {r['needICU.per100k.+30d']:.1f} / \
                        {r['needICU.per100k.+60d']:.1f}) \
                        ", axis=1))

pretty_cols['progress'] = 'Immunized <br> percentage <br> (+ in 14/30/60 days)'
df[pretty_cols['progress']] =(df.apply(lambda r: f" \
                        <b>{r['immune_ratio']:.2%}</b> <br> \
                        ({r['immune_ratio.+14d']:.1%} / \
                        {r['immune_ratio.+30d']:.1%} / \
                        {r['immune_ratio.+60d']:.1%})", axis=1))

df.sort_values('needICU.per100k', ascending=False)\
    [pretty_cols.values()]\
    .style.set_na_rep("-").set_properties(**{})
# -

# ### Assumtions and references:
# - Everything is pretty appoximate, I'm not an epidmiologist, just trying to get a guage of what's happening, how things are evolving, and what the future calculates to. The exact numbers may not be very important where differences between countries and policies have effects of multiple orders of magnitude.
# - Total case estimation is done from deaths by:
#     - Assuming that unbiased fatality rate is 1.5% (from heavily tested countries / Cruise ship) and that it takes 8 days on average for a case to go from being confirmed positive (after incubation + testing lag) to death. This is the same figure used by ["Estimating The Infected Population From Deaths"](https://covid19dashboards.com/covid-infected/) in this repo.
#     - Calculating the testing bias (8 days ago), and applying that bias to current cases figures for that country.
# - Projection is done using a simple SIR model with:
#     - Growth rate calculated by ratio of new cases in 5 past days, to new cases in the 5 days before that. This is pessimmistic - because it doesn't weigh the recent days heavier and because includes the testing rate growth rate as well, so is slow to react to both improvements in test coverage and "flattenning".
#     - Recovery probability being 1/20 (for 20 days to recover).
# - ICU need is calculated as being [6% of active cases](https://medium.com/@joschabach/flattening-the-curve-is-a-deadly-delusion-eea324fe9727) where:
#     - Active cases are taken from the SIR model (above).
#     - This is both pessimmistic - because real ICU rate may in reality be lower, due to testing biases, and especially in "younger" populations), and optimistic - because active cases which are on ICU take longer (so need the ICUs for longer).
#     - [Some numbers](https://www.forbes.com/sites/niallmccarthy/2020/03/12/the-countries-with-the-most-critical-care-beds-per-capita-infographic/) on actual capacity of ICUs per 100k (didn't find a full dataset for a lot of countries yet).
