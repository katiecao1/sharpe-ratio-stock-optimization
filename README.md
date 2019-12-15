# Sharpe Ratio Stock Optimization
> Using Python to create an investment portfolio among S&P 500 stocks that has the highest risk-adjusted returns

## Overview
This project seeks to find the portfolio with the optimal [Sharpe ratio](https://www.investopedia.com/terms/s/sharperatio.asp) using stocks from the S&P 500. To analyze the stocks, I use one-year historical daily data scraped from Yahoo Finance. The project will make use of SQL tables as I will store the data within a PostgreSQL server hosted by Heroku. Once the data has been successfully loaded, I will download the data back from Heroku to perform analysis on it.

> For code files, there are 5 Jupyter Notebooks arranged in order of steps
```shell
1. SP500_to_postgres.ipynb	Add files via upload	12 hours ago
2. Postgres_to_csv.ipynb	Add files via upload	2 days ago
3. Filter.ipynb	Add files via upload	2 days ago
4. Data Visualization.ipynb	Add files via upload	2 days ago
5. Portfolio Weights.ipynb
```

## Table of Contents
- [Getting the Data](#getting-the-data)
- [Filtering Stocks](#filtering-stocks)
- [Performing Analysis and Measurements](#performing-analysis-and-measurements)
- [Portfolio Construction](#portfolio-construction)
- [Conclusion](#conclusion)

## Step 1: Getting the Data
The first step was to web scrape the Yahoo Finance website for historical data for the S&P 500. I get a list of the S&P 500 by using python package Beautiful Soup to get the ticker information from Wikipedia. Then, I use this list to download the adjusted close price for the tickers using the Yahoo Finance REST API and the Python Requests library. Once I had the data, I created a data frame that has the adjusted close as the columns and the date as the rows. This data frame containing all adjusted close price will then be uploaded to the Heroku PostgreSQL server. 

## Step 2: Filtering Stocks
Creating a matrix of 500 x 500 would be a high computational cost. Therefore, I picked three methods to shortlist "better" stocks as followed.

### Method 1

The top stocks with the highest average daily returns.

### Method 2

The top 10 stocks with the smallest standard deviation of daily returns, assuming a lower standard deviation of daily returns equals less volatility. 

### Method 3

A common criticism of the sharpe ratio is that it only works with stocks whose returns are normally distributed. Hence, I came up with Filter 3.

Filter stocks with skewness in range of -0.8 to 0.8 and kurtosis -3.0 to 3.0 (Those are the classified parameters for a normal distribution). With Filter 3 I’re left with 232 stocks. However, for the time constraint of this project, I'm only going to use Filter 1 and Filter 2 for further analysis. Another option would be to apply Filter 3 first and then apply either Filter 1 or Filter 2.


## Step 3: Performing Analysis and Measurements
I then pulled all the data from Heroku Postgres server and saved it as a CSV file that I could easily convert into a data frame to perform further analysis. In this step, I constructed a class called stock_statistics to calculate the yearly return and volatility of each stock, the cumulative return of the timeframe provided, and the sharpe ratio for each stock based on the excess return and volatility. I also constructed a class to visualize the results. 

Since our data’s timeframe is exactly one year, I took the time series daily return (which was calculated using pct_change()), and compounded it for the entire year and minus one to get the geometric annualized return. I then calculated the standard deviation and annualized it by multiplying the square root of the length of the data frame (which is 251) to get the annualized volatility. Finally, I calculated the sharpe ratio by using the excess return, which is the yearly return minus the risk free rate (T-bill rate of 0.0212 on 6/22) , and divided by the volatility of each stock.

I calculated the cumulative return to see how stocks performed over a specific time period. It’s calculated by taking the daily return plus one and multiplies the daily return of the previous day until the end of the period. I later visualized the cumulative return and found out that it’s pretty flat year over year (6/2018 - 6/2019) since equity has a significant dip at the end of 2018 and it’s finally recovered after six months.
 
```python
class stock_statistics:
"""calculate stock statistics and return the sharpe ratio dataframe"""
    def __init__(self, df, risk_free):
        self.df = df
        self.risk_free = risk_free
    
    def process(self):
        self._dailyReturn()
        self._cumReturn()
        self._sharpeVolReturn()
        return self._sharpeVolReturn()
    
    def _dailyReturn(self):
        daily_return = self.df.pct_change()[1:]
        return daily_return
        
    def _cumReturn(self):
        """calculate cumulative returns for each stock and store in cum_return dataframe"""
        df = self._dailyReturn()  # make a copy 
        cum_return = pd.DataFrame()        
        col = df.columns #get column names
        for i in col:
            cum_return[i] = (1 + df[i])*df[i].shift()
        cum_return=cum_return[1:]
        return cum_return
    
    def _sharpeVolReturn(self):
        """calculate sharpe ratio, volatility, and yearly return of every stock"""
        df = self._dailyReturn() #make a copy
        stock_vol = df.std()*np.sqrt(252) 
        yearly_return = (df +1).product()-1
        sharpe_ratio = (yearly_return - self.risk_free)/stock_vol
        df_combined = pd.concat([stock_vol,yearly_return,sharpe_ratio],axis=1)
        df_combined.columns =['Yearly_Vol','Yearly_return','sharpe_ratio']
        return df_combined
```

In the visualization class, I graphed the statistics based on our sharpe ratio criteria. The libraries used include matplotlib and seaborn. I first defined a function to filter stocks with sharpe ratio to the level or range that I desire (i.e. over 2 or betIen 1.5 and 3). I then built the function to graph stocks’ daily return, price movement, cumulative return and yearly return over that period of time. 

Eventually, the user just needs to input the sharpe ratio criteria and update the risk free rate, and the class functions can be called to calculate and visualize the results. 

```python
class visualization:  
    def __init__(self, df, criteria, risk_free, filtered=True):
        self.df = df
        self.criteria = criteria
        self.risk_free = risk_free
        self.filtered = filtered
      
    def _filtered(self):
        """return a list of filtered stocks based on criteria"""
        df_filtered = stock_statistics(self.df, self.risk_free).process()
        filtered_stock_list = list(df_filtered.index[df_filtered['sharpe_ratio'] > self.criteria])
        return filtered_stock_list
 
    def _dailyReturnGraph(self):
        """need to input daily return dataframe"""
        plt.rcParams['figure.figsize'] = 8, 4
        if self.filtered:
            return stock_statistics(self.df, self.risk_free)._dailyReturn().loc[:, self._filtered()].plot();
        else:
            return stock_statistics(self.df, self.risk_free)._dailyReturn().plot();
        
    def _stockPriceGraph(self):
        """need to input stock price dataframe"""
        plt.rcParams['figure.figsize'] = 8, 4
        if self.filtered:
            return self.df.loc[:, self._filtered()].plot();
        else:
            return self.df.plot();
    
    def _cumReturnGraph(self):
        """need to input cum_return dataframe"""
        plt.rcParams['figure.figsize'] = 8, 4
        if self.filtered:
            return stock_statistics(self.df, self.risk_free)._cumReturn().loc[:, self._filtered()].plot();
        else:
            return stock_statistics(self.df, self.risk_free)._cumReturn().plot();
    
    def _yearlyReturn(self):
        plt.rcParams['figure.figsize'] = 8, 4
        sns.set(style="whitegrid")
        df_sharpe = stock_statistics(self.df, self.risk_free).process()
        if self.filtered:
            df_sharpe_sns = df_sharpe[df_sharpe['sharpe_ratio'] > self.criteria]
            return sns.barplot(x=df_sharpe_sns.index, y ='Yearly_return', data=df_sharpe_sns);
        else:
            return sns.barplot(x=df_sharpe.index, y ='Yearly_return', data=df_sharpe);
```    

Yearly return for highest Sharpe Ratio stocks:

![Yearly return for highest Sharpe Ratio stocks](https://github.com/katiecao1/sharpe-ratio-stock-optimization/blob/master/images/1.png)

In addition to using the highest Sharpe ratio as a filter, I also created filters for the highest mean return and the lowest standard deviations. These were calculated using the pandas built-in mean() and std() functions. I used the visualization class that I created earlier to show plots for daily return, stock price, cumulative return, and yearly return.

Yearly return for highest mean returns:

![Yearly return for highest mean returns](https://github.com/katiecao1/sharpe-ratio-stock-optimization/blob/master/images/2.png) 

Yearly return for lowest standard deviation of returns:

![Yearly return for lowest standard deviation of returns](https://github.com/katiecao1/sharpe-ratio-stock-optimization/blob/master/images/3.png) 

## Step 4: Portfolio Construction  
For each potential portfolio, I picked the top 4 for each criteria and performed analysis to find the optimal weights that maximize the Sharpe ratio. To find the optimal weights, multiple portfolios with random weights were generated. The return and volatility for these portfolios were charted and the shape formed from the plot is the efficient frontier. On the efficient frontier exists a portfolio with the maximum return over volatility ratio, which is the definition of the Sharpe ratio. 
I will use a hypothetical investment of $10,000 for each portfolio to compare its performance during the month of June 2019.


### Portfolio 1

Our Sharpe Ratio filter gave us the following weights:

| Stock ticker | AMT | BLL | CINF | SBUX |
| ------------ | --- | --- | ---- | ---- |
| Weight (%) | 32.55 | 34.49 | 16.29 | 16.67 |

If I actually allocated according to these weights to create a portfolio using a $10,000 investment, I would have a final balance of $10,699 for the month of June, a 6.99% return investment.

![Sharpe Ratio Filter](https://github.com/katiecao1/sharpe-ratio-stock-optimization/blob/master/images/4.png)

### Portfolio 2

4 Stocks with highest mean of daily return Our daily return mean filter gave us the following weights:

| Stock ticker | AMD | BLL | XLNX | SBUX |
| ------------ | --- | --- | ---- | ---- |
| Weight (%) | 24 | 59.98 | 2.96 | 36.80 |

This method would have a final balance of $11,264 over the month of June, a 12.64% return investment.

![Return Mean Filter](https://github.com/katiecao1/sharpe-ratio-stock-optimization/blob/master/images/5.png)

### Portfolio 3

Our standard deviation filter gave us the following weights:

| Stock ticker | RSG | EXC | DUK | NEE |
| ------------ | --- | --- | ---- | ---- |
| Weight (%) | 55.33 | 0.99 | 0.16 | 43.52 |

This method would have given us a $10,305 final balance, with a return of 3.05%.

![Standard Deviation Filter](https://github.com/katiecao1/sharpe-ratio-stock-optimization/blob/master/images/6.png)

## Conclusion
Out of the three portfolios, **the highest average daily return filter gave the best performance over the month of June 2019**. The stocks with the highest means can be very volatile, but optimizing the Sharpe ratio means that I am using diversification to minimize the effects of the individual stocks’ volatility. I would assume that the standard deviation filter would give us a lower return, but will most likely have the lowest portfolio volatility. The Sharpe ratio filter will most likely give us a portfolio that has better return than the standard deviation filter and lower volatility than the return mean filter. 

To fully draw conclusions for the dataset, I would want to continue our analysis for a year to see how the volatility and returns are affected.
