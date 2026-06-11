🚀 **From Raw Transactions to Retail Strategy: My Journey in the DQLab Python Hackathon!** 🚀

Solving real-world business challenges using data science is always incredibly rewarding. I recently participated in the **DQLab Python Hackathon**, where I built a retail performance analysis and *Market Basket Analysis* pipeline. 

The task was to identify **"Rising Star"** products (those with the fastest-growing sales trends) and design **"Potential Packaging"** (product bundles) to boost revenue.

In my initial iteration, my solution achieved a score of **84**. However, the most valuable part of this journey was what came next—comparing my approach with the judges' benchmark and diving deep into debugging to refine my code's logic.

💡 **Key Learnings, Implementations, & Code Refinements:**

1. **Trend Detection & Index Bug Correction (Rising Stars)**:
   I used a 3-day Moving Average to filter out daily sales noise and tracked consecutive growth trends for at least 12 active sales days. 
   *The Fix:* I identified and corrected an *off-by-one error* in the starting index of the growth streak calculation, which had previously caused the growth rate to be underestimated. Shifting the start index to `max_end - max_streak` made the growth percentage 100% mathematically exact.

2. **Market Basket Analysis Optimization (Apriori)**:
   I processed thousands of invoices to find purchase association patterns (Support >= 1% and Lift Ratio >= 2), and filtered rules containing Rising Star products.
   *The Fix:* To optimize performance, I replaced slow custom lambda groupings with Pandas' native `.unique()` method and streamlined the association rule filtering using vectorized frozenset operations (`isdisjoint()`).

3. **Data Visualization & Reporting**:
   I created a Relative Growth Index (Base 100) and actual sales visualizations using `matplotlib` to provide clear visual insights for business teams, exporting the final multi-sheet report directly into Excel (`retail_insight.xlsx`).

🔧 **The Biggest Challenge & Takeaway:**
Detecting consecutive growth streaks in volatile retail time-series data is tricky. Beyond the technicalities of time-series visualization without zero-fill noise, this project taught me the importance of constantly validating logical assumptions when translating raw data into real-world business decisions. 

A huge thank you to @DQLab for this outstanding challenge! It proved that debugging and refining your code is where the most meaningful learning happens.

Fellow data enthusiasts, have you ever discovered a hidden logic bug after comparing your code to a benchmark? Let’s connect and discuss in the comments! 👇

#HackathonDQLab #Python #DataScience #MarketBasketAnalysis #RetailAnalytics #AprioriAlgorithm #Debugging #GrowthMindset #MachineLearning
