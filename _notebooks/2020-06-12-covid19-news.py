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

# # World News from data (good & bad)
# > Signigicant changes vs. 10 days ago in transmission rates, ICU demand, and cases & deaths data.
#
# - categories: [world, overview, interactive, news]
# - permalink: /covid-news/
# - author: <a href=https://github.com/artdgn/>artdgn</a>
# - toc: true
# - image: images/news.png
# - hide: false

# > Warning: This dashboard was not built by an epidemiologist.
#

# +
#hide
import pandas as pd
import overview_helpers

stylers = overview_helpers.PandasStyling

# +
#hide
day_diff = 10

cur_data = overview_helpers.CovidData()
df_cur_all, debug_dfs = cur_data.table_with_projections(debug_dfs=True)
df_cur = cur_data.filter_df(df_cur_all)

past_data = overview_helpers.CovidData(-day_diff)
df_past = past_data.filter_df(past_data.table_with_projections())
# -

#hide_input
from IPython.display import Markdown
past_date = pd.to_datetime(past_data.dt_cols[-1]).date().isoformat()
Markdown(f"***Based on data up to: {cur_data.cur_date}. \
            Compared to ({day_diff} days before): {past_date}***")


#hide
df_data = df_cur.copy()
df_data['infection_rate_past'] = df_past['infection_rate']
df_data['infection_rate_past_err'] = df_past['growth_rate_std']
df_data['needICU.per100k_past'] = df_past['needICU.per100k']


# +
#hide
def index_format(df):
    df = cur_data.rename_long_names(df)
    df.index = df.apply(
        lambda s: f"""<font size=3><b>{s['emoji_flag']} {s.name}</b></font>""", axis=1)
    return df

def style_news_infections(df):
    cols = {
        'Cases.new.est': 'Estimated <br> <i>recent</i> cases <br> in last 5 days',
        'infection_rate': '<i>Current:</i><br>Estimated<br>daily<br>transmission<br>rate',
        'infection_rate_past': f'<i>{day_diff} days ago:</i><br>Estimated<br>daily<br>transmission<br>rate',
        'needICU.per100k': 'Estimated<br>current<br>ICU need<br>per 100k<br>population',
        'affected_ratio.est': 'Estimated <br><i>total</i><br>affected<br>population<br>percentage',
      }
    
    rate_norm = max(df['infection_rate'].max(), df['infection_rate_past'].max())
    return (index_format(df)[cols.keys()].rename(columns=cols).style
        .bar(subset=[cols['needICU.per100k']], color='#b21e3e', vmin=0, vmax=10)
        .bar(subset=cols['Cases.new.est'], color='#b57b17')
        .bar(subset=cols['affected_ratio.est'], color='#5dad64', vmin=0, vmax=1.0)
        .apply(stylers.add_bar, color='#f49d5a',
               s_v=df['infection_rate']/rate_norm, subset=cols['infection_rate'])
        .apply(stylers.add_bar, color='#d8b193',
               s_v=df['infection_rate_past']/rate_norm, subset=cols['infection_rate_past'])
        .format('<b>{:.2f}</b>', subset=[cols['needICU.per100k']])
        .format('<b>{:,.0f}</b>', subset=cols['Cases.new.est'])
        .format('<b>{:.1%}</b>', subset=[cols['affected_ratio.est'], 
                                         cols['infection_rate'],
                                         cols['infection_rate_past']], na_rep="-"))
        
def style_news_icu(df):
    cols = {
        'Cases.new.est': 'Estimated<br><i>recent</i>cases<br> in last 5 days',
        'needICU.per100k': '<i>Current:</i><br>Estimated<br>ICU need<br>per 100k<br>population',
        'needICU.per100k_past': f'<i>{day_diff} days ago:</i><br>Estimated<br>ICU need<br>per 100k<br>population',
        'infection_rate': 'Estimated<br>daily<br>transmission<br>rate',
        'affected_ratio.est': 'Estimated <br><i>total</i><br>affected<br>population<br>percentage',
      }
    
    return (index_format(df)[cols.keys()].rename(columns=cols).style
        .bar(subset=cols['needICU.per100k'], color='#b21e3e', vmin=0, vmax=10)
        .bar(subset=cols['needICU.per100k_past'], color='#c67f8e', vmin=0, vmax=10)
        .bar(subset=cols['Cases.new.est'], color='#b57b17')
        .bar(subset=cols['affected_ratio.est'], color='#5dad64', vmin=0, vmax=1.0)
        .apply(stylers.add_bar, color='#f49d5a',
               s_v=df['infection_rate']/df['infection_rate'].max(), 
               subset=cols['infection_rate'])
        .format('<b>{:.2f}</b>', subset=[cols['needICU.per100k'], cols['needICU.per100k_past']])
        .format('<b>{:,.0f}</b>', subset=cols['Cases.new.est'])
        .format('<b>{:.1%}</b>', subset=[cols['affected_ratio.est'], 
                                         cols['infection_rate']]))

def style_basic(df):
    cols = {
        'Cases.total.est': 'Estimated<br>total<br>cases',
        'Deaths.total': 'Total<br>reported<br>deaths',
        'last_case_date': 'Date<br>of last<br>reported case',
        'last_death_date': 'Date<br>of last<br>reported death',
      }  
    return (index_format(df)[cols.keys()].rename(columns=cols).style
        .format('<b>{:,.0f}</b>', subset=[cols['Cases.total.est'], cols['Deaths.total']]))

def emoji_flags(inds):
    return ' '.join(df_cur.loc[inds]['emoji_flag'])


# -

# # Transmission rate:
# > Note: "transmission rate" here is a measure of speed of spread of infection, and means how much of the susceptible population each infected person is infecting per day (if everyone is susceptible). E.g. 10% means that 100 infected patients will infect 10 new people per day. Related to [R0](https://en.wikipedia.org/wiki/Basic_reproduction_number). See [Methodology](#Methodology) for details of calculation.

# +
#hide
# optimistic rates
rate_past_opt = df_past['infection_rate'] - df_past['growth_rate_std']
rate_past_opt[rate_past_opt < 0] = 0
rate_cur_opt = df_cur['infection_rate'] - df_cur['growth_rate_std']
rate_cur_opt[rate_cur_opt < 0] = 0

rate_diff = rate_cur_opt - rate_past_opt
pct_rate_diff = rate_diff / df_past['growth_rate_std']
higher_trans = ((df_cur['infection_rate'] > 0.02) & 
        (df_cur['Cases.new.est'] > 100) &
        (rate_diff > 0.01) &
        (pct_rate_diff > 3))
new_waves = rate_diff[higher_trans].sort_values(ascending=False).index
# -

#hide_input
Markdown(f"## &#11093; Bad news: new waves ({emoji_flags(new_waves)})")

# > Large increase in transmission rate vs. 10 days ago, that might mean a relapse, new wave, worsening outbreak. 
#
# - Countries are sorted by size of change in transmission rate.
# - Includes only countries that were previously active (more than 100 estimated new cases).
# - "Large increase" = at least +1% change.

#hide_input
style_news_infections(df_data.loc[new_waves])

# +
#hide
import altair as alt
alt.data_transformers.disable_max_rows()

df_alt_all = pd.concat([d.reset_index() for d in debug_dfs], axis=0)

def infected_plots(countries, title, days_back=60):
    if not len(countries):
        return

    df_alt = df_alt_all[df_alt_all['day'].between(-days_back, 0) & 
                        (df_alt_all['country'].isin(countries))]

    select_country = alt.selection_single(
        name='Select',
        fields=['country'],
        bind='legend',
        empty='all',
        init={'country': countries[0]}
    )

    today_line = (alt.Chart(pd.DataFrame({'x': [-10]}))
                  .mark_rule(color='#c8d1ce')
                  .encode(x='x', strokeWidth=alt.value(6), opacity=alt.value(0.5)))
    
    lines = (alt.Chart(df_alt).mark_line().encode(
        x=alt.X('day:Q', 
                scale=alt.Scale(type='symlog'),
                axis=alt.Axis(labelOverlap='greedy', values=list(range(-days_back, 0, 5)),
                title=f'days relative to today ({cur_data.cur_date})')),
        y=alt.Y('Infected:Q',
                scale=alt.Scale(type='log'),
                axis=alt.Axis(format='%', title='Infected percentage'),
               ),
        color=alt.Color('country:N', 
                        legend=alt.Legend(title='Country',
                                          labelFontSize=14,
                                          values=countries.to_list())),
        opacity=alt.condition(select_country, alt.value(1), alt.value(0.4)),
        strokeWidth=alt.condition(select_country, alt.value(4), alt.value(2)))
     )

    return ((lines + today_line)
     .add_selection(select_country)
     .configure_title(fontSize=20)
     .configure_axis(labelFontSize=15, titleFontSize=18, grid=True)
     .properties(title=title, width=550, height=340).interactive(bind_x=False))


# -

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(new_waves, "Countries with new waves (vs. 10 days ago)")

#hide
lower_trans = ((df_cur['infection_rate'] > 0.02) & 
        (df_cur['Cases.new.est'] > 100) &
        (rate_diff < -0.01) &
        (pct_rate_diff < -3))
slowing_outbreaks = rate_diff[lower_trans].sort_values().index

#hide_input
Markdown(f"## &#128994; Good news: slowing waves ({emoji_flags(slowing_outbreaks)})")

# > Large decrease in transmission rate vs. 10 days ago, that might mean a slowing down / effective control measures.
#
# - Countries are sorted by size of change in transmission rate.
# - Includes only countries that were previously active (more than 100 estimated new cases).
# - "Large decrease" = at least -1% change.

#hide_input
style_news_infections(df_data.loc[slowing_outbreaks])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(slowing_outbreaks, "Countries with slowing waves (vs. 10 days ago)")

# # ICU need

# > Note: for details of ICU need calculation please see [Methodology](#Methodology).

#hide
icu_diff = df_cur['needICU.per100k'] - df_past['needICU.per100k']
icu_increase = icu_diff[icu_diff > 0.5].sort_values(ascending=False).index

#hide_input
Markdown(f"## &#11093; Bad news: higher ICU need ({emoji_flags(icu_increase)})")

# > Large increases in need for ICU beds per 100k population vs. 10 days ago.
#
# - Only countries for which the ICU need increased by more than 0.5 (per 100k).

#hide_input
style_news_icu(df_data.loc[icu_increase])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(icu_increase, "Countries with Higher ICU need (vs. 10 days ago)")

#hide
icu_decrease = icu_diff[icu_diff < -0.5].sort_values().index

#hide_input
Markdown(f"## &#128994; Good news: lower ICU need ({emoji_flags(icu_decrease)})")


# > Large decreases in need for ICU beds per 100k population vs. 10 days ago.
#
# - Only countries for which the ICU need decreased by more than 0.5 (per 100k).

#hide_input
style_news_icu(df_data.loc[icu_decrease])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(icu_decrease, "Countries with Lower ICU need (vs. 10 days ago)")

# # Cases and deaths

#hide
new_entries = df_cur.index[~df_cur.index.isin(df_past.index)]

#hide_input
Markdown(f"## &#11093; Bad news: new first significant outbreaks ({emoji_flags(new_entries)})")

# > Countries that have started their first significant outbreak (crossed 1000 total reported cases or 20 deaths) vs. 10 days ago.

#hide_input
style_news_infections(df_data.loc[new_entries])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(new_entries, "Countries with first large outbreak (vs. 10 days ago)")

#hide
significant_past = ((df_past['Cases.total.est'] > 1000) & (df_past['Deaths.total'] > 10))
active_in_past = ((df_past['Cases.new'] > 0) | (df_past['Deaths.new'] > 0))
no_cases_filt = ((df_cur['Cases.total'] - df_past['Cases.total']) == 0)
no_deaths_filt = ((df_cur['Deaths.total'] - df_past['Deaths.total']) == 0)
no_cases_and_deaths = df_cur.loc[no_cases_filt & no_deaths_filt & 
                                 significant_past & active_in_past].index

#hide_input
Markdown(f"## &#128994; Good news: no new cases or deaths ({emoji_flags(no_cases_and_deaths)})")

# > New countries with no new cases or deaths vs. 10 days ago.
#
# - Only considering countries that had at least 1000 estimated total cases and at least 10 total deaths and had and active outbreak previously.

#hide_input
style_basic(df_data.loc[no_cases_and_deaths])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(no_cases_and_deaths, "New countries with no new cases or deaths (vs. 10 days ago)")

#hide
no_deaths = df_cur.loc[no_deaths_filt & (~no_cases_filt) & 
                       significant_past & active_in_past].index

#hide_input
Markdown(f"## Mixed news: no new deaths, only new cases ({emoji_flags(no_deaths)})")

# > New countries with no new deaths (only new cases) vs. 10 days ago.
#
# - Only considering countries that had at least 1000 estimated total cases and at least 10 total deaths and had an active outbreak previously.

#hide_input
style_news_infections(df_data.loc[no_deaths])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(no_deaths, "Countries with only new cases (vs. 10 days ago)")

#hide
not_active = df_cur.loc[no_cases_filt & significant_past & ~active_in_past].index

#hide_input
Markdown(f"## No news: continously inactive countries ({emoji_flags(not_active)})")

# > Countries that had no new cases or deaths 10 days ago or now.
#
# - Only considering countries that had at least 1000 estimated total cases and at least 10 total deaths.
# - Caveat:  these countries may have stopped reporting data like [Tanzania](https://en.wikipedia.org/wiki/COVID-19_pandemic_in_Tanzania).

#hide_input
style_basic(df_data.loc[not_active])

# > Tip: Click country name in legend to switch countries. Uze mouse wheel to zoom Y axis.

#hide_input
infected_plots(not_active, "Continuosly inactive countries (now and 10 days ago)")

# # Appendix:

# > Note: For interactive map, per country details, projections, and modeling methodology see [Projections of ICU need by Country dashboard](/covid-progress-projections/)

# > Warning: the visualisation below contains the results of a predictive model that was not built by an epidemiologist.

# ## Future model projections plots per country
# > For countries in any of the above groups.

# > Tip: Choose country from the drop-down below the graph.

#hide_input
all_news = (new_waves, slowing_outbreaks, 
            icu_increase, icu_decrease,
            not_active, no_deaths, no_cases_and_deaths, new_entries)
news_countries = [c for g in all_news for c in g]
df_alt_filt = df_alt_all[(df_alt_all['day'] > -60) & 
                         (df_alt_all['country'].isin(news_countries))]
overview_helpers.altair_sir_plot(df_alt_filt, new_waves[0])

# ## Future World projections (all countries stacked)
# The outputs of the models for all countries in stacked plots.
# > Tip: Hover the mouse of the area to see which country is which and the countries S/I/R ratios at that point. 
#
# > Tip: The plots are zoomable and draggable.

#hide
df_tot = df_alt_all.rename(columns={'country': cur_data.COL_REGION}
                          ).set_index(cur_data.COL_REGION)
df_tot['population'] = df_cur_all['population']
for c in df_tot.columns[df_alt_all.dtypes == float]:
    df_tot[c + '-total'] = df_tot[c] * df_tot['population']
df_tot = df_tot.reset_index()
df_tot.columns = [c.replace('.', '-') for c in df_tot.columns]

# +
#hide
# filter by days
df_tot = df_tot[(df_tot['day'].between(-30, 30) & (df_tot['day'] % 3 == 0)) | (df_tot['day'] % 10 == 0)]

# filter out noisy countries for actively infected plot:
df_tot_filt = df_tot[df_tot[cur_data.COL_REGION].isin(df_cur.index.unique())]
# -

# ### World total estimated actively infected

# +
#hide_input
import altair as alt
alt.data_transformers.disable_max_rows()

# today
today_line = (alt.Chart(pd.DataFrame({'x': [0]}))
                  .mark_rule(color='orange')
                  .encode(x='x', size=alt.value(1)))

# make plot
max_y = df_tot_filt[df_tot_filt['day']==30]['Infected-total'].sum()
stacked_inf = alt.Chart(df_tot_filt).mark_area().encode(
    x=alt.X('day:Q',
            title=f'days relative to today ({cur_data.cur_date})',
            scale=alt.Scale(domain=(-30, 30))),
    y=alt.Y("Infected-total:Q", stack=True, title="Number of people",
           scale=alt.Scale(domain=(0, max_y))),
    color=alt.Color("Country/Region:N", legend=None),
    tooltip=['Country/Region', 'Susceptible', 'Infected', 'Removed'],    
)
(stacked_inf + today_line).interactive()\
.properties(width=650, height=340)\
.properties(title='Actively infected')\
.configure_title(fontSize=20)
# -

# ### World total estimated recovered or dead

# +
#hide_input
max_y = df_tot_filt[df_tot_filt['day']==30]['Removed-total'].sum()
stacked_rem = alt.Chart(df_tot_filt).mark_area().encode(
    x=alt.X('day:Q',
            title=f'days relative to today ({cur_data.cur_date})',
            scale=alt.Scale(domain=(-30, 30))),
    y=alt.Y("Removed-total:Q", stack=True, title="Number of people",
           scale=alt.Scale(domain=(0, max_y))),
    color=alt.Color("Country/Region:N", legend=None),
    tooltip=['Country/Region', 'Susceptible', 'Infected', 'Removed']
)

(stacked_rem + today_line).interactive()\
.properties(width=650, height=340)\
.properties(title='Recovered or dead')\
.configure_title(fontSize=20)
# -

# ## Methodology
# - I'm not an epidemiologist.
# - Tranmission rates calculation:
#     - Case growth rate is calculated over the 5 past days.
#     - Confidence bounds are calculated by from the weighted standard deviation of the growth rate over the last 5 days. Countries with highly noisy transmission rates are exluded from tranmission rate change tables ("new waves", "slowing waves"). 
#     - Tranmission rate is calculated from cases growth rate by estimating the actively infected population change relative to the susceptible population.
# - Recovery rate (for estimating actively infected): 
#   - Where the rate estimated from [Total Outstanding Cases](https://covid19dashboards.com/outstanding_cases/#Appendix:-Methodology-of-Predicting-Recovered-Cases) is too high (on down-slopes) recovery probability if 1/20 is used (equivalent 20 days to recover).
# - Total cases are estimated from the reported deaths for each country:
#     - Each country has different testing policy and capacity and cases are under-reported in some countries. Using an estimated IFR (fatality rate) we can estimate the number of cases some time ago by using the total deaths until today. We can than use this estimation to estimate the testing bias and multiply the current reported case numbers by that.
#     - IFRs for each country is estimated using the age IFRs from [May 1 New York paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3590771) and [UN demographic data for 2020](https://population.un.org/wpp/Download/Standard/Population/). These IFRs can be found in `df['age_adjusted_ifr']` column. Some examples: US - 0.98%, UK - 1.1%, Qatar - 0.25%, Italy - 1.4%, Japan - 1.6%.
#     - The average fatality lag is assumed to be 8 days on average for a case to go from being confirmed positive (after incubation + testing lag) to death. This is the same figure used by ["Estimating The Infected Population From Deaths"](https://covid19dashboards.com/covid-infected/).
#     - Testing bias: the actual lagged fatality rate is than divided by the IFR to estimate the testing bias in a country. The estimated testing bias then multiplies the reported case numbers to estimate the *true* case numbers (*=case numbers if testing coverage was as comprehensive as in the heavily tested countries*).
# - ICU need is calculated and age-adjusted as follows:
#     - UK ICU ratio was reported as [4.4% of active reported cases](https://www.imperial.ac.uk/media/imperial-college/medicine/sph/ide/gida-fellowships/Imperial-College-COVID19-NPI-modelling-16-03-2020.pdf).
#     - Using UKs ICU ratio and IFRs corrected for age demographics we can estimate each country's ICU ratio (the number of cases requiring ICU hospitalisation). For example using the IFR ratio between UK and Qatar to devide UK's 4.4% we get an ICU ratio of around 1% for Qatar which is also the ratio [they report to WHO here](https://apps.who.int/gb/COVID-19/pdf_files/30_04/Qatar.pdf).
#     - The ICU need is calculated from reported cases rather than from total estimated active cases. This is because the ICU ratio (4.4%) is based on reported cases.
