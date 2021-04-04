import pandas as pd
import plotly.express as px

url = 'https://health-infobase.canada.ca/src/data/covidLive/covid19-epiSummary-voc.csv'  

df = pd.read_csv(url)

prov_dict = {
	"AB" : "Alberta",
	"BC" : "British Columbia",
	"CA" : "Canada",
	"MB" : "Manitoba",	
	"NB" : "New Brunswick",
	"NL" : "Newfoundland and Labrador",
	"NS" : "Nova Scotia",
	"NT" : "Northwest Territories",
	"NU" : "Nunavut",
	"ON" : "Ontario",
	"PE" : "Prince Edward Island",
	"QC" : "Quebec",
	"SK" : "Saskatchewan",
	"YK" : "Yukon",
	"YT" : "Yukon"
}

dfuk = df.copy()
dfuk["Variant"] = "B.1.1.7 (UK)"
dfuk["Count"] = dfuk["b117"].fillna(0)

dfsa = df.copy()
dfsa["Variant"] = "B.1.351 (South Africa)"
dfsa["Count"] = dfsa["b1351"].fillna(0)

dfbr = df.copy()
dfbr["Variant"] = "P.1 (Brazil)"
dfbr["Count"] = dfbr["p1"].fillna(0)

dfvoc = dfuk.append(dfsa).append(dfbr)
dfvoc["Province"] = dfvoc.apply(lambda r: prov_dict[r["prov"]], axis=1)

dfvocmax = dfvoc.groupby(["Province", "Variant"]).max().reset_index() \
[["Province", "Variant", "Count"]] \
.rename(columns={"Count" : "MaxCount"}) 

dfvoc = pd.merge(dfvoc, dfvocmax, how="left", left_on=["Province", "Variant"], right_on=["Province", "Variant"])

dfprov = dfvoc[dfvoc["Province"] != "Canada"].sort_values(by=["Variant", "MaxCount", "report_date"], ascending=[True, False, True])

lineprov = px.line(dfprov, 
       x="report_date", y="Count", color="Variant", facet_row="Province",
       labels={"report_date" : "Time (Reported Date)", "Count" : "Cumulative cases", "Province" : "Province or Territory"},
       title="Cumulative cases infected with a Variant of Concern<br>over Time by Province or Territory by Variant",
       height=5000, template="simple_white"
      )


