import pandas as pd
import plotly.express as px

url = 'https://health-infobase.canada.ca/src/data/covidLive/covid19-epiSummary-voc.csv'  

df = pd.read_csv(url)

prov_dict = {
	"AB" : "Alberta",
	"BC" : "British Columbia",
	"NB" : "New Brunswick",
	"NL" : "Newfoundland and Labrador",
	"NS" : "Nova Scotia",
	"NT" : "Northwest Territories",
	"NU" : "Nunavut",
	"MB" : "Manitoba",
	"ON" : "Ontario",
	"PE" : "Prince Edward Island",
	"QC" : "Quebec",
	"SK" : "Saskatchewan",
	"YK" : "Yukon"
}
dfuk = df.copy()
dfuk["Variant"] = "B.1.1.7 (United Kingdom)"
dfuk["Count"] = dfuk["b117"].fillna(0)

dfsa = df.copy()
dfsa["Variant"] = "B.1.351 (South Africa)"
dfsa["Count"] = dfsa["b1351"].fillna(0)

dfbr = df.copy()
dfbr["Variant"] = "P.1 (Brazil)"
dfbr["Count"] = dfbr["p1"].fillna(0)

dfvoc = dfuk.append(dfsa).append(dfbr)
dfvoc["Total"] = dfvoc.apply(lambda r: r["b117"] + r["b1351"] + r["p1"], axis=1)

#dfvoc = dfvoc.sort_values(by=["Total", "Variant"], ascending=[False, True])

dfprov = dfvoc[dfvoc["prov"] != "CA"].sort_values(by=["Variant", "report_date"], ascending=[True, True])

lineprov = px.line(dfprov, 
       x="report_date", y="Count", color="Variant", facet_row="prov",
        height=8000, title="Variants over time"
      )


