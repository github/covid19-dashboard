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
# # Per country projections of ICU need and total affected population percentage
# > Modeling current and future ICU demand and percentage of affected population. 
#
# - comments: true
# - categories: [overview]
# - author: artdgn
# - image: images/covid-progress-projections.png
# - permalink: /covid-progress-projections/
# - toc: true
# - hide: false
# -

# > Note: This dashboard contains the results of a predictive model. The author has tried to make it as accurate as possible. But the COVID-19 situation is changing quickly, and these models inevitably include some level of speculation. 

# + papermill={"duration": 0.330834, "end_time": "2020-03-27T06:31:16.261108", "exception": false, "start_time": "2020-03-27T06:31:15.930274", "status": "completed"} tags=[]
#hide
import pandas as pd
import overview_helpers

helper = overview_helpers.OverviewDataExtras
df = helper.filter_df(helper.table_with_projections())
df.columns
# -

# ## Top 20 by estimated need for ICU beds
# - ICU need is estimated as [6% of active cases](https://medium.com/@joschabach/flattening-the-curve-is-a-deadly-delusion-eea324fe9727).
# - ICU capacities are from [Wikipedia](https://en.wikipedia.org/wiki/List_of_countries_by_hospital_beds) (OECD countries mostly) and [CCB capacities in Asia](https://www.researchgate.net/publication/338520008_Critical_Care_Bed_Capacity_in_Asian_Countries_and_Regions).
# - ICU spare capacity is based on 70% normal occupancy rate ([66% in US](https://www.sccm.org/Blog/March-2020/United-States-Resource-Availability-for-COVID-19), [75% OECD](https://www.oecd-ilibrary.org/social-issues-migration-health/health-at-a-glance-2019_4dd50c09-en))
# - Details of estimation and prediction calculations are in [Appendix](#appendix).
# - Column definitions:
#     - **Estimated ICU need per 100k population**: number of ICU beds estimated to be needed per 100k population by COVID-19 patents.
#     - **Projected in 14 days**: projected ICU need per 100k population in 14 days.
#     - **Projected in 30 days**: projected ICU need per 100k population in 30 days.
#     - **ICU capacity per 100k**: number of ICU beds per 100k population.
#     - **Estimated ICU Spare capacity per 100k**: estimated ICU capacity per 100k population based on assumed normal occupancy rate of 70% and number of ICU beds (only for countries with ICU beds data).
#     - **Estimated daily case growth rate**: percentage daily change in total cases during last 5 days.
# > Tip: The <b><font color="b21e3e">red (need for ICU)</font></b>  and the <b><font color="3ab1d8">blue (ICU spare capacity)</font></b>  bars are on the same 0-10 scale, for easy visual comparison of columns.

#hide_input
rename_cols = {'needICU.per100k': 'Estimated <br> ICU need <br> per 100k <br> population',
               'needICU.per100k.+14d': 'Projected <br> In 14 days', 
               'needICU.per100k.+30d': 'Projected <br> In 30 days',               
               'icu_capacity_per100k': 'ICU <br> capacity <br> per 100k',
               'icu_spare_capacity_per100k': 'Estimated ICU <br> Spare capacity <br> per 100k',               
               'growth_rate': 'Estimated <br> daily case <br> growth rate',
              }
icu_cols = list(rename_cols.values())[:3]
df_icu_bars = df.rename(rename_cols, axis=1)
df_icu_bars.sort_values(rename_cols['needICU.per100k'], ascending=False)\
[rename_cols.values()]\
.head(20).style\
    .bar(subset=icu_cols[0], color='#b21e3e', vmin=0, vmax=10)\
    .bar(subset=icu_cols[1], color='#f43d64', vmin=0, vmax=10)\
    .bar(subset=icu_cols[2], color='#ef8ba0', vmin=0, vmax=10)\
    .bar(subset=[rename_cols['icu_spare_capacity_per100k']], color='#3ab1d8', vmin=0, vmax=10)\
    .applymap(lambda _: 'color: blue', subset=[rename_cols['icu_spare_capacity_per100k']])\
    .bar(subset=[rename_cols['growth_rate']], color='#d65f5f', vmin=0, vmax=0.33)\
    .format('<b>{:.1%}</b>', subset=[rename_cols['growth_rate']])\
    .format('<b>{:.1f}</b>', subset=[rename_cols['icu_capacity_per100k']], na_rep="-")\
    .format('<b>{:.1f}</b>', subset=[rename_cols['icu_spare_capacity_per100k']], na_rep="-")\
    .format('<b>{:.2f}</b>', subset=icu_cols)\
    .set_precision(2)

# ## Affected population percentages in top 20 countries with most estimated new cases
# - Sorted by number of estimated new cases during the last 5 days.
# - Details of estimation and prediction calculations are in [Appendix](#appendix).
# - Column definitions:
#     - **Estimated <i>new</i> cases in last 5 days**: estimated new cases in last 5 days.
#     - **Estimated <i>total</i> affected population percentage**: estimated percentage of total population already affected (infected, recovered, or dead).
#     - **Projected in 14 days**: projected percentage of total affected population in 14 days.
#     - **Projected in 30 days**: projected percentage of total affected population in 30 days.
#     - **Reported fatality percentage**: reported total deaths divided by total cases.
#     - **Estimated daily case growth rate**: percentage daily change in total cases during last 5 days.
#

#hide_input
rename_cols = {'Cases.new.est': 'Estimated <br> <i>new</i> cases <br> in last 5 days', 
               'affected_ratio.est': 'Estimated <br> <i>total</i> affected <br> population <br> percentage',
               'affected_ratio.est.+14d': 'Projected <br> In 14 days',
               'affected_ratio.est.+30d': 'Projected <br> In 30 days',
               'Fatality Rate': 'Reported <br> fatality <br> percentage',
               'growth_rate': 'Estimated <br> daily case <br> growth rate',
              }
progress_cols = list(rename_cols.values())[:4]
df_progress_bars = df.rename(rename_cols, axis=1)
df_progress_bars.sort_values(rename_cols['Cases.new.est'], ascending=False)\
[rename_cols.values()]\
.head(20).style\
    .bar(subset=progress_cols[0], color='#b57b17')\
    .bar(subset=progress_cols[1], color='#5dad64', vmin=0, vmax=1.0)\
    .bar(subset=progress_cols[2], color='#719974', vmin=0, vmax=1.0)\
    .bar(subset=progress_cols[3], color='#a1afa3', vmin=0, vmax=1.0)\
    .bar(subset=[rename_cols['Fatality Rate']], color='#420412', vmin=0, vmax=0.1)\
    .applymap(lambda _: 'color: red', subset=[rename_cols['Fatality Rate']])\
    .bar(subset=[rename_cols['growth_rate']], color='#d65f5f', vmin=0, vmax=0.33)\
    .format('<b>{:,.0f}</b>', subset=list(rename_cols.values())[0])\
    .format('<b>{:.1%}</b>', subset=list(rename_cols.values())[1:])

# ## Full table with more details
#  - Contains reported data, estimations, projections, and numbers relative to population.
#  - This is a busy table in order to present as many stats as possible for each country for people to be able to inspect their counties of interest in maximum amount detail (without running the code).
#  - Sorted by projected need for ICU beds per 100k in 14 days. 
#  - **New** in this table means **during last 5 days**.
#  - Includes only countries with at least 10 deaths.
#  > Tip: use Ctrl + F to find your country of interest in the table.

# +
#hide_input
pretty_cols = {}

pretty_cols['cases'] = 'Cases <br> - Reported (+new) <br> - <i> Estimated (+new) </i>'
df[pretty_cols['cases']] =(df.apply(lambda r: f" \
                         {r['Cases.total']:,.0f} \
                         (+<b>{r['Cases.new']:,.0f}</b>) <br>\
                         <i>{r['Cases.total.est']:,.0f} \
                         (+<b>{r['Cases.new.est']:,.0f}</b></i> )\
                         ", axis=1))

pretty_cols['progress'] = ('Affected <br> percentage <br> \
                      - Reported <br> - <i>Estimated <br> Now / in <b>14</b> / 30 days</i>')
df[pretty_cols['progress']] =(df.apply(lambda r: f" \
                        {r['affected_ratio']:.2%} <br>\
                        <i>{r['affected_ratio.est']:.2%} \
                        <b>{r['affected_ratio.est.+14d']:.1%}</b> / \
                        {r['affected_ratio.est.+30d']:.1%}</i>", axis=1))

pretty_cols['icu'] = ('Estimated <br> Need for ICU <br> per 100k <br>\
                      Now <i> / in <b>14</b> / 30 days</i>')
df[pretty_cols['icu']] =(df.apply(lambda r: f"\
                        {r['needICU.per100k']:.2f} / \
                        <i><b>{r['needICU.per100k.+14d']:.1f}</b> / \
                        {r['needICU.per100k.+30d']:.1f}</i>", axis=1))

pretty_cols['deaths'] = 'Reported <br> Deaths <br> - Total (+new) <br> - <i>Per100k (+new)</i>'
df[pretty_cols['deaths']] =(df.apply(lambda r: f" \
                         {r['Deaths.total']:,.0f} \
                         (+<b>{r['Deaths.new']:,.0f}</b>) <br> \
                         <i>{r['Deaths.total.per100k']:,.1f} \
                         (+<b>{r['Deaths.new.per100k']:,.1f}</b></i>) \
                         ", axis=1))

df.sort_values('needICU.per100k.+14d', ascending=False)\
    [pretty_cols.values()]\
    .style.set_na_rep("-").set_properties(**{})
# -

# <a id='appendix'></a>
# ## Appendix
# - I'm not an epidemiologist. This is an attempt to understand what's happening, and what the future looks like if current trends remain unchanged.
# - Everything is approximated and depends heavily on underlying assumptions.
# - Total case estimation calculated from deaths by:
#     - Assuming that unbiased fatality rate is 1.5% (from heavily tested countries / the cruise ship data) and that it takes 8 days on average for a case to go from being confirmed positive (after incubation + testing lag) to death. This is the same figure used by ["Estimating The Infected Population From Deaths"](https://covid19dashboards.com/covid-infected/) in this repo.
#     - Testing bias: the actual lagged fatality rate is than divided by the 1.5% figure to estimate the testing bias in a country. The estimated testing bias then multiplies the reported case numbers to estimate the *true* case numbers (*=case numbers if testing coverage was as comprehensive as in the heavily tested countries*).
#     - The testing bias calculation is a high source of uncertainty in all these estimations and projections. Better source of testing bias (or just *true case* numbers), should make everything more accurate.
# - Projection is done using a simple [SIR model](https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology#The_SIR_model) with (see [examples](#examples)) combined with the approach in [Total Outstanding Cases](https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases):
#     - Growth rate calculated over the 5 past days. This is pessimistic - because it includes the testing rate growth rate as well, and is slow to react to both improvements in test coverage and "flattening" due to social isolation.
#     - Recovery probability being 1/20 (for 20 days to recover) where the rate estimated from [Total Outstanding Cases](https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases) is too high (on down-slopes).
# - ICU need is calculated as being [6% of active cases](https://medium.com/@joschabach/flattening-the-curve-is-a-deadly-delusion-eea324fe9727) where:
#     - Active cases are taken from the SIR model.
#     - This is both pessimistic - because real ICU rate may in reality be lower, due to testing biases, and especially in "younger" populations), and optimistic - because active cases which are on ICU take longer (so need the ICUs for longer).
#     - ICU capacities are from [Wikipedia](https://en.wikipedia.org/wiki/List_of_countries_by_hospital_beds) (OECD countries mostly) and [CCB capacities in Asia](https://www.researchgate.net/publication/338520008_Critical_Care_Bed_Capacity_in_Asian_Countries_and_Regions).
#     - ICU spare capacity is based on 70% normal occupancy rate ([66% in US](https://www.sccm.org/Blog/March-2020/United-States-Resource-Availability-for-COVID-19), [75% OECD](https://www.oecd-ilibrary.org/social-issues-migration-health/health-at-a-glance-2019_4dd50c09-en))

# <a id='examples'></a>
# ### Examples of modeling plots 
# - For the 5 countries with highest estimated number of new cases.
# > Note: The purpose is to demonstrate the actual calculations used in the tables above and the dynamics of the model.

#hide_input
sir_plot_countries = df.sort_values('Cases.new.est', ascending=False).head(5).index
helper.table_with_projections(plot_countries=sir_plot_countries);
