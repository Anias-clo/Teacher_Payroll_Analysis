sns.countplot(data=df,
              x='Fiscal Year',
              hue='Delta Category');

sns.countplot(data=df,
              x='Fiscal Year',
              hue='Compensation at or Above Schedule Rate');

sns.set_style("whitegrid")
sns.barplot(data=df_rate_summary,
            x='Fiscal Year',
            y='Effective Rate',
            hue='Employment Category');