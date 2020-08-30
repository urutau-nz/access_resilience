#imports
import utils
from config import *


def plotting(nearest_service, demo, db, context):
    '''plots ecdf'''

    demo = demo.drop(['gid', 'median_age'], axis=1)
    demo = demo.replace(['C'], 0).apply(lambda x: np.int64(x))
    services = nearest_service.dest_type.unique()
    for service in tqdm(services):
        df = nearest_service.loc[nearest_service['dest_type'] == service]
        hist_total = []
        hist_euro = []
        hist_maori = []
        hist_pacific = []
        hist_asian = []
        hist_melaa = []
        for i in range(len(df)):
            hist_total = hist_total + [df.distance.iloc[i]]*demo.population.iloc[i]
            hist_euro = hist_euro + [df.distance.iloc[i]]*demo.pop_euro.iloc[i]
            hist_maori = hist_maori + [df.distance.iloc[i]]*demo.pop_maori.iloc[i]
            hist_pacific = hist_pacific + [df.distance.iloc[i]]*demo.pop_pacific.iloc[i]
            hist_asian = hist_asian + [df.distance.iloc[i]]*demo.pop_asian.iloc[i]
            hist_melaa = hist_melaa + [df.distance.iloc[i]]*demo.pop_melaa.iloc[i]

        # Initialize figure
        fig = go.Figure()
        # Add Traces
        fig.add_scatter(x=np.unique(hist_total), y=ecdf(hist_total)(np.unique(hist_total)), name='Total',
                        line_shape='hv', line=dict(color="green"))
        fig.add_scatter(x=np.unique(hist_euro), y=ecdf(hist_euro)(np.unique(hist_euro)), name='NZ European',
                       line_shape='hv', line=dict(color="white"))
        fig.add_scatter(x=np.unique(hist_maori), y=ecdf(hist_maori)(np.unique(hist_maori)), name='Maori',
                       line_shape='hv', line=dict(color="black"))
        fig.add_scatter(x=np.unique(hist_pacific), y=ecdf(hist_pacific)(np.unique(hist_pacific)), name='Pasifika',
                        line_shape='hv', line=dict(color="red"))
        fig.add_scatter(x=np.unique(hist_asian), y=ecdf(hist_asian)(np.unique(hist_asian)), name='Asian',
                       line_shape='hv', line=dict(color="blue"))
        fig.add_scatter(x=np.unique(hist_melaa), y=ecdf(hist_melaa)(np.unique(hist_melaa)), name='Middle Eastern, Latin American or African',
                       line_shape='hv', line=dict(color="yellow"))

        # Set title
        fig.update_layout(
            title_text="{} Access Distribution: {}".format(service, context['city']),
            xaxis_title="Distance to nearest {} (m)".format(service),
            yaxis_title="Percentage of Population (0-1)",
            xaxis_domain=[0.05, 1],
            xaxis=dict(
            range=[0,10000]
            ),
            legend=dict(
            x=0.75,
            y=0.25,
            traceorder='normal',
            font=dict(
            size=20,),
            ),
        )
        #add spike lines
        fig.update_xaxes(showspikes=True)
        fig.update_yaxes(showspikes=True)
        plotly.offline.plot(fig, filename='results/{}_liquefaction_exposure.html'.format(service))


#ecdf function
def ecdf(x):
    x = np.sort(x)
    def result(v):
        return np.searchsorted(x, v, side='right') / x.size
    return result
