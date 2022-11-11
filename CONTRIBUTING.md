# Contributing To This Project

We highly encourage contributions to this project and welcome PRs.

Familiarity with [fastpages](https://github.com/fastai/fastpages) is helpful.  All you need to do is include the appropriate front matter in your notebook.  See [this guide](https://github.com/fastai/fastpages#customizing-blog-posts-with-front-matter). 

**A good pull request to emulate is [this one](https://github.com/github/covid19-dashboard/pull/33)** - study the Jupyter notebook closely, especially the first cell that specifies the metadata, and how cells are hidden with `#hide` or `#hide_input`.

You should preview your dashboard locally by following [the Development Guide](https://github.com/fastai/fastpages/blob/master/_fastpages_docs/DEVELOPMENT.md), before submitting a PR.

# Guidelines For New Dashboards

- Your dashboard should not duplicate or present substantially the same information to what already exists in other dashboards.
- Any technical information and notes should go in an appendix.
- Limit the amount of information presented to one narrow, logical subject. We encourage hiding extraneous information as that can be viewed in the source notebook if necessary.
- Make the visualization as approachable as possible.  Explain things in plain English.  Font sizes should be easy to read. 
- Put your main visualization at the top of your notebook.  The methodology or "how to" should either be in footnotes or hidden from view.
- Dashboards that present a predictive model will attract additional scrutiny and review.  If models are too complex to be understood, or not presented clearly - we may decide it is not appropriate for this site.  Furthermore, analysis containing predictive models will be displayed with appropriate warnings to set expectations.

