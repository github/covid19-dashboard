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

# + [markdown] papermill={"duration": 0.016043, "end_time": "2020-04-21T12:16:32.969003", "exception": false, "start_time": "2020-04-21T12:16:32.952960", "status": "completed"} tags=[]
# # Projections of ICU need by Country
# > Modeling current and future ICU demand.
#
# - categories: [overview, map, interactive]
# - author: <a href=https://github.com/artdgn/>artdgn</a>
# - image: images/covid-progress-projections.png
# - permalink: /covid-progress-projections/
# - toc: true
# - hide: false

# + [markdown] papermill={"duration": 0.011416, "end_time": "2020-04-21T12:16:32.991324", "exception": false, "start_time": "2020-04-21T12:16:32.979908", "status": "completed"} tags=[]
# > Warning: This analysis contains the results of a predictive model that was not prepared or reviewed by an epidemiologist. The assumptions and methods presented should be considered carefully before arriving at any conclusions. 

# + execution={"iopub.execute_input": "2020-04-21T12:16:33.017500Z", "iopub.status.busy": "2020-04-21T12:16:33.016736Z", "iopub.status.idle": "2020-04-21T12:16:44.018439Z", "shell.execute_reply": "2020-04-21T12:16:44.019026Z"} papermill={"duration": 11.017858, "end_time": "2020-04-21T12:16:44.019212", "exception": false, "start_time": "2020-04-21T12:16:33.001354", "status": "completed"} tags=[]
#hide
import pandas as pd
import overview_helpers

helper = overview_helpers.OverviewData
stylers = overview_helpers.PandasStyling
df_all = helper.table_with_projections()
df_all.columns

# + execution={"iopub.execute_input": "2020-04-21T12:16:44.049495Z", "iopub.status.busy": "2020-04-21T12:16:44.048737Z", "iopub.status.idle": "2020-04-21T12:16:44.052619Z", "shell.execute_reply": "2020-04-21T12:16:44.051788Z"} papermill={"duration": 0.021948, "end_time": "2020-04-21T12:16:44.052729", "exception": false, "start_time": "2020-04-21T12:16:44.030781", "status": "completed"} tags=[]
#hide_input
from IPython.display import Markdown
Markdown(f"***Based on data up to: {pd.to_datetime(helper.dt_today).date().isoformat()}***")
# -

#hide
geo_helper = overview_helpers.GeoMap
df_geo = geo_helper.make_geo_df(df_all, cases_filter=1000, deaths_filter=20)
fig = geo_helper.make_map_figure(df_geo)

#hide_input
fig.update_layout(
    updatemenus=[
        dict(
            buttons=[
                geo_helper.button_dict(
                    df_geo['needICU.per100k'], 'ICU need<br>(current)', 
                    colorscale='Sunsetdark', scale_max=10,
                    subtitle='Estimated current ICU need per 100k population'),
                geo_helper.button_dict(
                    df_geo['needICU.per100k.+14d'],  'ICU need<br>(in 14 days)', 
                    colorscale='Sunsetdark', scale_max=10,
                    subtitle='Projected ICU need per 100k population in 14 days',
                    err_series=df_geo['needICU.per100k.+14d.err']),
                geo_helper.button_dict(
                    df_geo['needICU.per100k.+30d'],  'ICU need<br>(in 30 days)', 
                    colorscale='Sunsetdark', scale_max=10,
                    subtitle='Projected ICU need per 100k population in 30 days',
                    err_series=df_geo['needICU.per100k.+30d.err']),
                geo_helper.button_dict(
                    df_geo['icu_capacity_per100k'], 'ICU Capacity', colorscale='Blues',
                    subtitle='ICU capacity per 100k population'),
            ],
            direction="down", bgcolor='#efdaee',
            pad={"r": 10, "t": 10},
            showactive=False, x=0.07, xanchor="left", y=1.1, yanchor="top"),
        dict(
            buttons=[
                geo_helper.button_dict(
                    df_geo['affected_ratio.est'], 'Affected percent<br>(Current)', 
                    colorscale='Bluyl', percent=True,
                    subtitle='Estimated current affected population percentage'),
                geo_helper.button_dict(
                    df_geo['affected_ratio.est.+14d'], 'Affected percent<br>(in 14 days)', 
                    colorscale='Bluyl', scale_max=25, percent=True,
                    subtitle='Projected affected population percentage in 14 days',
                    err_series=df_geo['affected_ratio.est.+14d.err']),
                geo_helper.button_dict(
                    df_geo['affected_ratio.est.+30d'], 'Affected percent<br>(in 30 days)', 
                    colorscale='Bluyl', scale_max=25, percent=True,
                    subtitle='Projected affected population percentage in 30 days',
                    err_series=df_geo['affected_ratio.est.+30d.err']),
                geo_helper.button_dict(
                    df_geo['Cases.total.per100k.est'], 'Total cases<br>estimated per 100k', 
                    colorscale='YlOrRd',
                    subtitle='Estimated total cases per 100k population'),
                geo_helper.button_dict(
                    df_geo['Cases.total.est'], 'Total cases<br>(estimated)', colorscale='YlOrRd',
                    subtitle='Estimated total cases'),
                geo_helper.button_dict(
                    df_geo['Cases.total.per100k'], 'Total cases<br>reported per 100k', 
                    colorscale='YlOrRd',
                    subtitle='Reported total cases per 100k population'),
                geo_helper.button_dict(
                    df_geo['Cases.total'], 'Total cases<br>(reported)', colorscale='YlOrRd',
                    subtitle='Reported total cases'),
            ],
            direction="down", bgcolor='#dceae1',
            pad={"r": 10, "t": 10},
            showactive=False, x=0.24, xanchor="left", y=1.1, yanchor="top"),
        dict(
            buttons=[
                geo_helper.button_dict(
                    df_geo['infection_rate'], 'Infection rate<br>percent (blue-red)',
                    colorscale='Bluered', scale_max=10, percent=True,
                    subtitle='Infection spread rate: over 5% (red) spreading, under 5% (blue) recovering',
                    err_series=df_geo['growth_rate_std']),
                geo_helper.button_dict(
                    df_geo['infection_rate'], 'Infection rate<br>percent', 
                    colorscale='YlOrRd', scale_max=33, percent=True,
                    subtitle='Infection spread rate (related to R0)',
                    err_series=df_geo['growth_rate_std']),
                geo_helper.button_dict(
                    df_geo['Cases.new.per100k.est'], 'New cases<br>estimated per 100k', 
                    colorscale='YlOrRd',
                    subtitle='Estimated new cases in last 5 days per 100k population'),
                geo_helper.button_dict(
                    df_geo['Cases.new.est'], 'New cases<br>(estimated)', 
                    colorscale='YlOrRd',
                    subtitle='Estimated new cases in last 5 days'),
                geo_helper.button_dict(
                    df_geo['Cases.new.per100k'], 'New cases<br>reported per 100k', 
                    colorscale='YlOrRd',
                    subtitle='Reported new cases in last 5 days per 100k population'),
                geo_helper.button_dict(
                    df_geo['Cases.new'], 'New cases<br>(reported)', 
                    colorscale='YlOrRd',
                    subtitle='Reported new cases in last 5 days'),
            ],
            direction="down", bgcolor='#efe9da',
            pad={"r": 10, "t": 10},
            showactive=False, x=0.46, xanchor="left", y=1.1, yanchor="top"),
        dict(
            buttons=[
                geo_helper.button_dict(
                    df_geo['Deaths.total.per100k'], 'Deaths<br>per 100k', colorscale='Reds',
                    subtitle='Total deaths per 100k population'),
                geo_helper.button_dict(
                    df_geo['Deaths.total'], 'Deaths<br>Total', colorscale='Reds',
                    subtitle='Total deaths'),
                geo_helper.button_dict(
                    df_geo['Deaths.new.per100k'], 'New deaths<br>per 100k', colorscale='Reds',
                    subtitle='New deaths in last 5 days per 100k population'),
                geo_helper.button_dict(
                    df_geo['Deaths.new'], 'New deaths<br>total', colorscale='Reds',
                    subtitle='New deaths in last 5 days'),
                geo_helper.button_dict(
                    df_geo['lagged_fatality_rate'], 'Fatality rate %<br>(lagged)', 
                    colorscale='Reds', scale_max=20, percent=True,
                    subtitle='Reported fatality rate (relative to reported cases 8 days ago)'),
            ],
            direction="down", bgcolor='#efdbda',
            pad={"r": 10, "t": 10},
            showactive=False, x=0.68, xanchor="left", y=1.1, yanchor="top"),
    ]);

# # World map (interactive)
# > Includes only countries with at least 1000 reported cases or at least 20 reported deaths.
#
# - Details of estimation and prediction calculations are in [Appendix](#methodology) and in [Tables](#tables), as well as [Plots of model predictions](#examples).
# - New cases and new deaths refer to cases or deaths in the last 5 days.

# > Tip: Select columns to show on map to from the dropdown menus. The map is zoomable and draggable.

#hide_input
# from IPython.display import HTML
# HTML(fig.to_html())
fig.show()

# + [markdown] papermill={"duration": 0.01049, "end_time": "2020-04-21T12:16:44.072280", "exception": false, "start_time": "2020-04-21T12:16:44.061790", "status": "completed"} tags=[]
# # Tables
# <a id='tables'></a>
# ## Projected need for ICU beds
#
# > Countries sorted by current ICU demand, split into Growing and Recovering countries by current infection rate.
#
# - Details of estimation and prediction calculations are in [Appendix](#methodology), as well as [Plots of model predictions](#examples).
# - Column definitions:
#     - <font size=2><b>Estimated ICU need per 100k population</b>: number of ICU beds estimated to be needed per 100k population by COVID-19 patents.</font>
#     - <font size=2><b>Estimated daily infection rate</b>: daily percentage rate of new infections relative to active infections during last 5 days.</font>
#     - <font size=2><b>Projected ICU need per 100k in 14 days</b>: self explanatory.</font>
#     - <font size=2><b>Projected ICU need per 100k in 30 days</b>: self explanatory.</font>
#     - <font size=2><b>ICU capacity per 100k</b>: number of ICU beds per 100k population.</font>
#     - <font size=2><b>Estimated ICU Spare capacity per 100k</b>: estimated ICU capacity per 100k population based on assumed normal occupancy rate of 70% and number of ICU beds (only for countries with ICU beds data).</font>

# + [markdown] papermill={"duration": 0.009167, "end_time": "2020-04-21T12:16:44.092197", "exception": false, "start_time": "2020-04-21T12:16:44.083030", "status": "completed"} tags=[]
# > Tip: The <b><font color="b21e3e">red (need for ICU)</font></b>  and the <b><font color="3ab1d8">blue (ICU spare capacity)</font></b>  bars are on the same 0-10 scale, for easy visual comparison of columns.
# -

#hide
df = helper.filter_df(df_all)

# + execution={"iopub.execute_input": "2020-04-21T12:16:44.124650Z", "iopub.status.busy": "2020-04-21T12:16:44.119771Z", "iopub.status.idle": "2020-04-21T12:16:44.991670Z", "shell.execute_reply": "2020-04-21T12:16:44.992136Z"} papermill={"duration": 0.890669, "end_time": "2020-04-21T12:16:44.992275", "exception": false, "start_time": "2020-04-21T12:16:44.101606", "status": "completed"} tags=[]
#hide
df_data = df.sort_values('needICU.per100k', ascending=False)
df_pretty = df_data.copy()
df_pretty['needICU.per100k.+14d'] = stylers.with_errs_float(
    df_pretty, 'needICU.per100k.+14d', 'needICU.per100k.+14d.err')
df_pretty['needICU.per100k.+30d'] = stylers.with_errs_float(
    df_pretty, 'needICU.per100k.+30d', 'needICU.per100k.+30d.err')
df_pretty['infection_rate'] = stylers.with_errs_ratio(df_pretty, 'infection_rate', 'growth_rate_std')

cols = {'needICU.per100k': 'Estimated<br>current<br>ICU need<br>per 100k<br>population',
        'infection_rate': 'Estimated<br>daily infection<br>rate',
       'needICU.per100k.+14d': 'Projected<br>ICU need<br>per 100k<br>In 14 days', 
       'needICU.per100k.+30d': 'Projected<br>ICU need<br>per 100k<br>In 30 days',               
       'icu_capacity_per100k': 'ICU<br>capacity<br> per 100k',
       'icu_spare_capacity_per100k': 'Estimated ICU<br>Spare capacity<br>per 100k',               
      }

def style_icu_table(df_pretty, filt):
    return df_pretty[filt][cols.keys()].rename(cols, axis=1).style\
        .bar(subset=cols['needICU.per100k'], color='#b21e3e', vmin=0, vmax=10)\
        .apply(stylers.add_bar, color='#f43d64',
               s_v=df_data[filt]['needICU.per100k.+14d']/10, subset=cols['needICU.per100k.+14d'])\
        .apply(stylers.add_bar, color='#ef8ba0',
               s_v=df_data[filt]['needICU.per100k.+30d']/10, subset=cols['needICU.per100k.+30d'])\
        .apply(stylers.add_bar, color='#f49d5a',
               s_v=df_data[filt]['infection_rate']/0.33, subset=cols['infection_rate'])\
        .bar(subset=[cols['icu_spare_capacity_per100k']], color='#3ab1d8', vmin=0, vmax=10)\
        .applymap(lambda _: 'color: blue', subset=cols['icu_spare_capacity_per100k'])\
        .format('<b>{:.1f}</b>', subset=cols['icu_capacity_per100k'], na_rep="-")\
        .format('<b>{:.1f}</b>', subset=cols['icu_spare_capacity_per100k'], na_rep="-")\
        .format('<b>{:.2f}</b>', subset=cols['needICU.per100k'])


# -

# ### Growing countries (infection rate above 5%)

#hide_input
style_icu_table(df_pretty, df_data['infection_rate'] > 0.05)

# ### Recovering countries (infection rate below 5%)

#hide_input
style_icu_table(df_pretty, df_data['infection_rate'] <= 0.05)

# + [markdown] papermill={"duration": 0.013253, "end_time": "2020-04-21T12:16:45.018802", "exception": false, "start_time": "2020-04-21T12:16:45.005549", "status": "completed"} tags=[]
# # Appendix
# <a id='appendix'></a>

# + [markdown] papermill={"duration": 0.013516, "end_time": "2020-04-21T12:16:45.047181", "exception": false, "start_time": "2020-04-21T12:16:45.033665", "status": "completed"} tags=[]
# <a id='examples'></a>
#
# ## Interactive plot of Model predictions
#
# > Tip: Choose a country from the drop-down menu to see the calculations used in the tables above and the dynamics of the model.

# + execution={"iopub.execute_input": "2020-04-21T12:16:45.087905Z", "iopub.status.busy": "2020-04-21T12:16:45.087062Z", "iopub.status.idle": "2020-04-21T12:17:00.351387Z", "shell.execute_reply": "2020-04-21T12:17:00.351941Z"} papermill={"duration": 15.291152, "end_time": "2020-04-21T12:17:00.352091", "exception": false, "start_time": "2020-04-21T12:16:45.060939", "status": "completed"} tags=[]
#hide_input
_, debug_dfs = helper.table_with_projections(debug_dfs=True)
df_alt = pd.concat([d.reset_index() for d in debug_dfs], axis=0)
overview_helpers.altair_sir_plot(df_alt, df['needICU.per100k.+14d.min'].idxmax())

# + [markdown] papermill={"duration": 0.120423, "end_time": "2020-04-21T12:17:00.635637", "exception": false, "start_time": "2020-04-21T12:17:00.515214", "status": "completed"} tags=[]
# ## Projected Affected Population percentage
# > Countries sorted by number of new cases in last 5 days. The projected affected population percentage is directly related to the calculation of estimated ICU need.

# + [markdown] papermill={"duration": 0.127632, "end_time": "2020-04-21T12:17:00.889117", "exception": false, "start_time": "2020-04-21T12:17:00.761485", "status": "completed"} tags=[]
# - Details of estimation and prediction calculations are in [Appendix](#methodology), as well as [Plots of model predictions](#examples).
# - Column definitions:
#    - <font size=2><b>Estimated <i>new</i> cases in last 5 days</b>: self explanatory.</font>
#    - <font size=2><b>Estimated <i>total</i> affected population percentage</b>: estimated percentage of total population already affected (infected, recovered, or dead).</font>
#    - <font size=2><b>Estimated daily infection rate</b>: daily percentage rate of new infections relative to active infections during last 5 days.</font>
#    - <font size=2><b>Projected total affected percentage in 14 days</b>: of population.</font>
#    - <font size=2><b>Projected total affected percentage in 30 days</b>: of population.</font>        
#    - <font size=2><b>Lagged fatality rate</b>: reported total deaths divided by total cases 8 days ago.</font>

# + execution={"iopub.execute_input": "2020-04-21T12:17:01.170022Z", "iopub.status.busy": "2020-04-21T12:17:01.169348Z", "iopub.status.idle": "2020-04-21T12:17:01.631320Z", "shell.execute_reply": "2020-04-21T12:17:01.631845Z"} papermill={"duration": 0.60958, "end_time": "2020-04-21T12:17:01.632016", "exception": false, "start_time": "2020-04-21T12:17:01.022436", "status": "completed"} tags=[]
#hide_input
df_data = df.sort_values('Cases.new.est', ascending=False).head(20)
df_pretty = df_data.copy()
df_pretty['affected_ratio.est.+14d'] = stylers.with_errs_ratio(
    df_pretty, 'affected_ratio.est.+14d', 'affected_ratio.est.+14d.err')
df_pretty['affected_ratio.est.+30d'] = stylers.with_errs_ratio(
    df_pretty, 'affected_ratio.est.+30d', 'affected_ratio.est.+30d.err')
df_pretty['infection_rate'] = stylers.with_errs_ratio(df_pretty, 'infection_rate', 'growth_rate_std')

cols = {'Cases.new.est': 'Estimated <br> <i>new</i> cases <br> in last 5 days',        
       'affected_ratio.est': 'Estimated <br><i>total</i><br>affected<br>population<br>percentage',
       'infection_rate': 'Estimated <br>daily infection<br>rate',
       'affected_ratio.est.+14d': 'Projected<br><i>total</i><br>affected<br>percentage<br>In 14 days',
       'affected_ratio.est.+30d': 'Projected<br><i>total</i><br>affected<br>percentage<br>In 30 days',       
       'lagged_fatality_rate': 'Lagged<br>fatality<br>rate',
      }

df_pretty[cols.keys()].rename(cols, axis=1).style\
    .apply(stylers.add_bar, color='#719974',
           s_v=df_data['affected_ratio.est.+14d'], subset=cols['affected_ratio.est.+14d'])\
    .apply(stylers.add_bar, color='#a1afa3',
           s_v=df_data['affected_ratio.est.+30d'], subset=cols['affected_ratio.est.+30d'])\
    .apply(stylers.add_bar, color='#f49d5a',
           s_v=df_data['infection_rate']/0.33, subset=cols['infection_rate'])\
    .bar(subset=cols['Cases.new.est'], color='#b57b17')\
    .bar(subset=cols['affected_ratio.est'], color='#5dad64', vmin=0, vmax=1.0)\
    .bar(subset=cols['lagged_fatality_rate'], color='#420412', vmin=0, vmax=0.2)\
    .applymap(lambda _: 'color: red', subset=cols['lagged_fatality_rate'])\
    .format('<b>{:,.0f}</b>', subset=cols['Cases.new.est'])\
    .format('<b>{:.1%}</b>', subset=[cols['lagged_fatality_rate'], cols['affected_ratio.est']])

# + [markdown] papermill={"duration": 0.12762, "end_time": "2020-04-21T12:17:01.880996", "exception": false, "start_time": "2020-04-21T12:17:01.753376", "status": "completed"} tags=[]
# ## Methodology & Assumptions
# <a id='methodology'></a>
# - I'm not an epidemiologist. This is an attempt to understand what's happening, and what the future looks like if current trends remain unchanged.
# - Everything is approximated and depends heavily on underlying assumptions.
# - Countries with less than 10 total deaths or less than 1 Million population are excluded. 
# - Projection is done using a simple [SIR model](https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology#The_SIR_model) with (see [examples](#examples)) combined with the approach in [Total Outstanding Cases](https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases):
#     - Growth rate calculated over the 5 past days. This is pessimistic - because it includes the testing rate growth rate as well, and is slow to react to both improvements in test coverage and "flattening" due to social isolation.
#     - Confidence bounds are calculated by from the weighted STD of the growth rate over the last 5 days. Model predictions are calculated for growth rates within 1 STD of the weighted mean. The maximum and minimum values for each day are used as confidence bands.
#     - For projections (into future) very noisy projections (with broad confidence bounds) are not shown in the tables.
#     - Recovery probability being 1/20 (for 20 days to recover) where the rate estimated from [Total Outstanding Cases](https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases) is too high (on down-slopes).  
# - ICU need is calculated as being [4.4% of active reported cases](https://www.imperial.ac.uk/media/imperial-college/medicine/sph/ide/gida-fellowships/Imperial-College-COVID19-NPI-modelling-16-03-2020.pdf) where:
#     - Active cases are taken from the SIR model. The ICU need is calculated from reported cases rather than from total estimated active cases. This is because the ICU ratio (4.4%) is based on symptomatic reported cases.
#     - ICU capacities are from [Wikipedia](https://en.wikipedia.org/wiki/List_of_countries_by_hospital_beds) (OECD countries mostly) and [CCB capacities in Asia](https://www.researchgate.net/publication/338520008_Critical_Care_Bed_Capacity_in_Asian_Countries_and_Regions).
#     - ICU spare capacity is based on 70% normal occupancy rate ([66% in US](https://www.sccm.org/Blog/March-2020/United-States-Resource-Availability-for-COVID-19), [75% OECD](https://www.oecd-ilibrary.org/social-issues-migration-health/health-at-a-glance-2019_4dd50c09-en))
# - Total case estimation calculated from deaths by:
#     - Assuming that unbiased fatality rate is 0.72% ([current meta estimate in](https://www.cebm.net/covid-19/global-covid-19-case-fatality-rates/)). 
#     - The average fatality lag is assumed to be 8 days on average for a case to go from being confirmed positive (after incubation + testing lag) to death. This is the same figure used by ["Estimating The Infected Population From Deaths"](https://covid19dashboards.com/covid-infected/).
#     - Testing bias: the actual lagged fatality rate is than divided by the 0.72% figure to estimate the testing bias in a country. The estimated testing bias then multiplies the reported case numbers to estimate the *true* case numbers (*=case numbers if testing coverage was as comprehensive as in the heavily tested countries*).
#     - The testing bias calculation is a high source of uncertainty in all these estimations and projections. Better source of testing bias (or just *true case* numbers), should make everything more accurate.  
