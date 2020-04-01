{# D, table, newcases, np, pd  #}
{% set COL_REGION = COL_REGION or 'Country/Region' %}
{% set KPI_CASE = KPI_CASE or 'World' %}
{% set KPIS_INFO = KPIS_INFO or [{'title': 'China', 'prefix': 'China'}, {'title': 'Europe', 'prefix': 'EU'}, {'title': 'U.S.', 'prefix': 'US'}] %}
{% set LEGEND_DOMAIN = LEGEND_DOMAIN or [10, 100, 1000, np.inf] %}
{% set WIDTH_REGION, WIDTH_STRIP = 120, 140 %}
{% set STRIP_WIDTH = (WIDTH_REGION // newcases.shape[1] + 1) %}
{% set LEGEND_RANGE = ['rgba(255, 152, 0, 0.1)', 'rgba(255, 152, 0, 0.4)', 'rgba(255, 152, 0, 0.7)', 'rgba(255, 152, 0, 1)'] %}
{% set TOPLINKS = TOPLINKS or [
  {'title': 'World', 'href': '../covid-overview/'}, {'title': 'US', 'href': '../covid-overview-us/'},
  {'title': 'Europe', 'href': '../covid-overview-europe/'}] %}
{% set lastdays = (D['updated'] - D['since']).days %}

{% macro kpi(name, number, growth, growcls='') -%}
  <div class="kpi">
    <div class="kname">{{ name }}</div>
    <div class="num">{{ '{0:,.0f}'.format(number) }}</div>
    <div class="grow {{ growcls }}">(<b>{{ '{0:+,.0f}'.format(growth) }}</b>)</div>
  </div>
{%- endmacro %}

{% macro kpiblocksm(prefix='', title=KPI_CASE) -%}
  <div class="kpi-sm">
    <div class="kpi-hed">{{ title }}</div>
    <div class="d-flex kpi-box">
      {{ kpi(name='Cases', number=D[prefix + ' Cases'], growth=D[prefix + ' Cases (+)']) }}
      {{ kpi(name='Deaths', number=D[prefix + ' Deaths'], growth=D[prefix + ' Deaths (+)']) }}
    </div>
  </div>
{%- endmacro %}

{% macro toplinks() -%}
<div class="text-center toplinksgithub">
  {% for link in TOPLINKS %}<a href="{{ link['href'] }}">{{ link['title'] }}</a>{% endfor %}
</div>
{%- endmacro %}

{% macro narrative() -%}
{% if KPI_CASE == 'World' %}
  In the last <b>{{ lastdays }} days</b>, <b class="color-neg">{{ '{0:,.0f}'.format(D['Cases (+)']) }}</b> new Coronavirus cases have been reported worldwide.
  Of which <b class="color-neg">{{ '{0:,.0f}'.format(D['EU Cases (+)']) }}</b> ({{ "{0:.0%}".format(D['EU Cases (+)'] / D['Cases (+)']) }}) are from <b>Europe</b>.
  <b>China</b> has reported <b class="color-neg">{{ '{0:,.0f}'.format(D['China Cases (+)']) }}</b> new cases in the last {{ lastdays }} days.
{% elif KPI_CASE == 'US' %}
  In the last <b>{{ lastdays }} days</b>, <b class="color-neg">{{ '{0:,.0f}'.format(D['Cases (+)']) }}</b> new Coronavirus cases have been reported in the US.
  Of which <b class="color-neg">{{ '{0:,.0f}'.format(D['NY Cases (+)']) }}</b> ({{ "{0:.0%}".format(D['NY Cases (+)'] / D['Cases (+)']) }}) are from <b>New York</b> State.
  <b>Washington</b> has reported <b class="color-neg">{{ '{0:,.0f}'.format(D['WA Cases (+)']) }}</b> new cases in the last {{ lastdays }} days.
{% elif KPI_CASE == 'Europe' %}
  In the last <b>{{ lastdays }} days</b>, <b class="color-neg">{{ '{0:,.0f}'.format(D['Cases (+)']) }}</b> new Coronavirus cases have been reported in the Europe.
  Of which <b class="color-neg">{{ '{0:,.0f}'.format(D['IT Cases (+)']) }}</b> ({{ "{0:.0%}".format(D['IT Cases (+)'] / D['Cases (+)']) }}) are from <b>Italy</b>.
  <b>Spain</b> has reported <b class="color-neg">{{ '{0:,.0f}'.format(D['SP Cases (+)']) }}</b> new cases in the last {{ lastdays }} days.
{% elif KPI_CASE == 'Asia' %}
  In the last <b>{{ lastdays }} days</b>, <b class="color-neg">{{ '{0:,.0f}'.format(D['Cases (+)']) }}</b> new Coronavirus cases have been reported in Asia.
  Of which <b class="color-neg">{{ '{0:,.0f}'.format(D['CN Cases (+)']) }}</b> ({{ "{0:.0%}".format(D['CN Cases (+)'] / D['Cases (+)']) }}) are from <b>China</b>.
  <b>India</b> has reported <b class="color-neg">{{ '{0:,.0f}'.format(D['IN Cases (+)']) }}</b> new cases in the last {{ lastdays }} days.
{% else %}
  ''
{% endif %}
{%- endmacro %}

{% macro plotstrip(arr) -%}
  <div class="d-flex" style="height:15px;">
    {% set colors = np.digitize(arr, LEGEND_DOMAIN) %}
    {% for i, v in enumerate(arr) %}
    <div style="width:{{ STRIP_WIDTH }}px;background:{{ LEGEND_RANGE[colors[i]] if (v) else '#eee' }};border-right:1px solid rgba(255,255,255,0.5);"></div>
    {% endfor %}
  </div>
{%- endmacro %}

{% macro legend() -%}
<svg width="100" height="20" viewBox="0,0,100,20" style="overflow: visible; display: block;">
  <g>
    {% for i, _ in enumerate(LEGEND_DOMAIN) %}
    <rect x="{{ 25 * i }}"  y="8" width="25" height="10" fill="{{ LEGEND_RANGE[i] }}"></rect>
    {% endfor %}
  </g>
  <g style="font-size:10px;text-anchor:middle;">
    {% for i, x in enumerate(LEGEND_DOMAIN[:-1], 1) %}
    <g transform="translate({{ 25 * i }}, 6)"><text>{{ x }}</text></g>
    {% endfor %}
    </g>
</svg>
{%- endmacro %}

<div class="overview">
  {{ toplinks() }}
  <div>
    <div class="kpi-hed text-center">{{ KPI_CASE }}</div>
    <div class="d-flex kpi-box">
      {{ kpi(name='Confirmed Cases', number=D['Cases'], growth=D['Cases (+)']) }}
      {{ kpi(name='Deaths', number=D['Deaths'], growth=D['Deaths (+)']) }}
    </div>
  </div>
  <p class="text-center text-uppercase fs9">Updated on <b>{{ D['updated'].strftime('%B %d, %Y') }}</b> ( +change since {{ lastdays }} days ago.)</p>
  <div class="d-flex" style="justify-content:space-between;">
    {% for kpi in KPIS_INFO %}
    {{ kpiblocksm(**kpi) }}
    {% endfor %}
  </div>
  <p class="text-center" style="font-size: 14px;max-width: 400px;">{{ narrative() }}</p>
  <table class="table" style="width:575px;">
    <thead>
      <tr>
        <th class="text-right" style="width:{{ WIDTH_REGION }}px;"></th>
        <th class="text-left" style="width:{{ WIDTH_STRIP }}px;">{{ legend() }}</th>
        <th colspan="7"></th>
      </tr>
      <tr>
        <th class="text-right" style="width:{{ WIDTH_REGION }}px;">{{ {'Country/Region': 'Country', 'Province/State': 'State'}.get(COL_REGION, 'Location') }}</th>
        <th class="text-left" style="width:{{ WIDTH_STRIP }}px;">New Cases</th>
        <th class="text-left" colspan="2">Total Cases</th>
        <th colspan="2">Deaths</th>
        <th class="fs9" >Fatality</th>
      </tr>
    </thead>
    <tbody>
      <tr style="font-size:9px;">
        <td></td>
        <td style="display:flex;justify-content:space-between;">
          <div>{{ pd.to_datetime(newcases.columns[0]).strftime('%b. %d') }}</div>
          <div>{{ pd.to_datetime(newcases.columns[-1]).strftime('%b. %d') }}</div>
        </td>
        <td></td>
        <td colspan="4" class="text-left change" style="font-size: 9px;">(+NEW) since {{ D['since'].strftime('%b, %d') }}</td>
        <td></td>
        <td></td>
      </tr>
    {% for index, row in table.iterrows() %}
      <tr>
        <td class="mw"><b>{{ row[COL_REGION] }}</b></td>
        <td style="vertical-align: middle;">{{ plotstrip(arr=newcases.loc[row[COL_REGION]].values) }}</td>
        <td class="pl1"><b>{{ '{0:,.0f}'.format(row['Cases']) }}</b></td>
        <td class="change neg">(<b>{{ '{0:+,.0f}'.format(row['Cases (+)']) }}</b>)</td>
        <td class="pl1">{{ '{0:,.0f}'.format(row['Deaths']) }}</td>
        <td class="change neg">(<b>{{ '{0:+,.0f}'.format(row['Deaths (+)']) }}</b>)</td>
        <td class="pl1">{{ row['Fatality Rate'] }}%</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</div>
<style>
.overview {
  min-width: 500px;
  font-size: 10px;
  font-family: "Segoe UI", SegoeUI, Roboto, "Segoe WP", "Helvetica Neue", "Helvetica", "Tahoma", "Arial", sans-serif !important;
}
.overview .toplinksgithub a {
  background: #d3d3d3;
  font-size: 14px;
  color: #1d87ae;
  margin: 10px;
  padding: 2px 10px;
}
.overview p {
  margin: 6px auto !important;
  padding: 0;
}
@media screen and (max-width: 660px) {
  .overview p { max-width: none !important; }
}
.overview b {
  font-weight: bolder;
}
.overview .kpi-hed {
  font-weight: bold;
  font-size: 20px;
}
.overview .kpi-box {
  justify-content: space-around;
  background: #ececec;
  padding: 10px 0 !important;
  margin: 5px 0 !important;
  min-width: 180px;
}
.overview .kpi .num {
  font-size: 40px;
  line-height: 40px;
  font-weight: bold;
}
.overview .kpi .grow {
  line-height: 12px;
  font-size: 12px;
}
.overview .table .change.pos , .overview .kpi .grow.pos {
  color: #118822;
}
.overview .table .change.neg, .overview .kpi .grow, .color-neg {
  color: #cc1100;
}
.overview p .color-neg {
  background: #ececec;
  padding: 0 5px;
}
.overview .kpi .kname {
  font-size: 12px;
}
.overview .kpi-sm .kpi-hed {
  font-size: 14px;
  line-height: 10px;
  padding-top: 10px !important;
}
.overview .kpi-sm .num {
  font-size: 20px;
  line-height: 20px;
}
.overview .kpi-sm .kname {
  font-size: 11px;
  line-height: 10px;
}
.overview .table {
  border-collapse: collapse;
  margin: auto !important;
  text-align: right;
  margin-top: 14px;
  color: black;
  font-size: 13px;
  display: table !important;
}
.overview .table .change {
  color: #999;
  font-size: 80%;
  text-align: start;
  vertical-align: inherit;
  font-weight: normal;
  padding-left: 1px !important;
}
.overview .table th {
  font-weight: normal;
}
.overview .table tbody tr {
  border-bottom: 1px solid #eee;
  background: none;
}
.overview .table td, .overview .table th {
  padding: 1px 1px 1px 10px !important;
  vertical-align: middle;
  border: none;
  background: none;
}
.overview .table th {
  text-align: center;
  text-transform: uppercase;
}
.overview .table thead {
  border-bottom: 1px solid black;
}
.overview .fs9 {
  font-size: 9px;
}
.overview .d-flex {
  display: flex;
}
.overview .text-center { text-align: center !important; }
.overview .text-left { text-align: left !important; }
.overview .text-right { text-align: right !important; }
.overview .text-uppercase { text-transform: uppercase !important; }
.overview div {
  margin: 0 !important;
  padding: 0 !important;
}
</style>