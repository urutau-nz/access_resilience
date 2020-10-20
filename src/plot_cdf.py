#imports
import utils
from config import *


def plotting(baseline_nearest, nearest_matrix, demo, db, context, hazard_type, nsim, pop_group='total'):
    '''plots ecdf'''
    #remove rows with 0 population from each df
    zero_pop = demo.loc[demo['total'] == 0]
    zero_pop_id_flt = zero_pop['id_orig'].tolist()
    #convert to ints
    zero_pop_id_int = [int(i) for i in zero_pop_id_flt]
    #convert to str
    zero_pop_id_str = [str(i) for i in zero_pop_id_int]
    baseline_nearest = baseline_nearest[~baseline_nearest['id_orig'].isin(zero_pop_id_str)]
    nearest_matrix = nearest_matrix[~nearest_matrix['id_orig'].isin(zero_pop_id_str)]
    demo = demo[~demo['id_orig'].isin(zero_pop_id_flt)]
    #get list of different services
    services = context['services']
    for service in services:
        baseline = baseline_nearest.loc[baseline_nearest['dest_type'] == service]
        sim = nearest_matrix.loc[nearest_matrix['dest_type'] == service]
        hist_baseline = []
        hist_mean = []
        hist_upper = []
        hist_lower = []

        for i in range(len(baseline)):
            hist_baseline = hist_baseline + [baseline['distance'].iloc[i]]*demo[pop_group].iloc[i]
            id = baseline.id_orig.iloc[i] #if we end up closing origins add in an if clause to avoid errors?
            dist_subset = sim.distance.loc[sim['id_orig'] == id]
            hist_mean = hist_mean + [dist_subset.mean()]*demo[pop_group].iloc[i]
            hist_upper = hist_upper + [dist_subset.quantile(0.05)]*demo[pop_group].iloc[i]
            hist_lower = hist_lower + [dist_subset.quantile(0.95)]*demo[pop_group].iloc[i]
        # Initialize figure
        fig = go.Figure()
        # Add Traces
        fig.add_trace(go.Scatter(x=np.unique(hist_baseline), y=ecdf(hist_baseline)(np.unique(hist_baseline)), name='Baseline',
                        line_shape='hv', line=dict(color="green", shape='hv')))
        fig.add_trace(go.Scatter(x=np.unique(hist_mean), y=ecdf(hist_mean)(np.unique(hist_mean)), name='Post {} mean'.format(hazard_type),
                        line_shape='hv', line=dict(color="red", shape='hv')))
        fig.add_trace(go.Scatter(x=np.unique(hist_upper), y=ecdf(hist_upper)(np.unique(hist_upper)),
                        line=dict(color='red', width=0), name='90% confidence interval'))
        fig.add_trace(go.Scatter(x=np.unique(hist_lower), y=ecdf(hist_lower)(np.unique(hist_lower)),
                        line=dict(color='red', width=0), fill='tonexty', fillcolor='rgba(255, 0, 0, 0.2)', name='lower bound', showlegend=False))

        # Set title
        fig.update_layout(
            title_text="{} Access Distribution: {}\n Simulations: {}".format(service.title(), context['city'].title(), nsim),
            xaxis_title="Distance to nearest {} (m)".format(service.title()),
            yaxis_title="Percentage of Population (0-1)",
            xaxis_domain=[0.05, 1],
            xaxis=dict(
            range=[0,10000]
            ),
            showlegend=True,
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
        plotly.offline.plot(fig, filename='results/{}_{}_{}_access_{}_exposure.html'.format(context['city'], pop_group, service, hazard_type))


#ecdf function
def ecdf(x):
    x = np.sort(x)
    def result(v):
        return np.searchsorted(x, v, side='right') / x.size
    return result
