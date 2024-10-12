# Bank of America Digital Transformation

The aim of this project is to find the digital transformation journey of Bank of America (BOA). The way I tackled this was through looking into the 9000+ patents from BOA. The patents were sorted into classes where the unclassed patents are classed using the output vector from a BERT model with the use of KNN.


## File breakdown:

1. `BOA_patent.ipynb` contains the code for the analysis of the patents.
2. `patent_scrapper.py` contains the script for scraping the patents. To use this make sure to download and configure the chromium engine. [Chromium Engine](https://developer.chrome.com/docs/chromedriver/get-started)
3. The scrapped patents are stored in the `data` folder.

