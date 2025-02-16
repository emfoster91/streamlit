import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

def AgGrid_default(DF):
        gb = GridOptionsBuilder.from_dataframe(DF)
        gb.configure_grid_options(enableRangeSelection=True)
        
        for col in DF.columns:
                if (col!='Renamer') & (col!='Y'):
                    gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="£", aggFunc='max')
                    
        out = AgGrid(DF,
        gridOptions=gb.build(),
        fill_columns_on_grid_load=True,
        height=min(400,32*(len(DF)+1)),
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True
        )

        return out

def dc_page():

    # Radio for user to choose view
    view = st.radio('Choose View:',['Lollipop','Tables'], horizontal=True)

    # User Input Year
    year_list = [2017,2018,2019,2020,2021,2022]
    select_year = st.selectbox('Select Year',year_list,year_list.index(2022))

    DM = st.session_state.DM
    DM['Y'] = DM['Y'].astype(int)
    DM = DM.sort_values(by=['Credit Amount'], ascending=False)

    # Filter for selected year or year prior to that
    selected_data = DM[(DM['Y']==select_year) | (DM['Y']==(select_year-1))]

    # Sum over all Source Types
    df = selected_data.groupby(['Renamer','Y']).sum().reset_index()

    # Pivot from long to wide format: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot.html
    output = df.pivot(index='Renamer',columns='Y',values='Credit Amount').reset_index().fillna(0)

    # Calculate change
    output['Delta'] = output[select_year] - output[(select_year-1)]

    #Sort by absolute values: https://stackoverflow.com/questions/30486263/sorting-by-absolute-value-without-changing-the-data
    output = output.reindex(output['Delta'].abs().sort_values(ascending=False).index)

    if view=='Lollipop':

        #https://towardsdatascience.com/lollipop-dumbbell-charts-with-plotly-696039d5f85

        st.subheader("Change from previous year's giving:")
        
        #st.slider docs: https://docs.streamlit.io/library/api-reference/widgets/st.slider
        x = st.slider('', min_value=-60000, max_value=60000,value=[1000,60000],step=500)

        filtered_output = output[(output['Delta']>=x[0]) & (output['Delta']<=x[1])]

        filtered_output = filtered_output.reindex(filtered_output['Delta'].abs().sort_values().index)

        # Isolate Selected year data and year prior to that
        syd = filtered_output[select_year].tolist() 
        sydm1 = filtered_output[(select_year-1)].tolist()

        fig3= go.Figure()

        # Selected Year Scatter
        fig3.add_trace(go.Scatter(x = syd, 
                                y = filtered_output['Renamer'],
                                mode = 'markers',
                                marker_color = 'darkblue',
                                marker_size = 10,
                                name = select_year))
        
        # Prior Year Scatter
        fig3.add_trace(go.Scatter(x = sydm1, 
                                y = filtered_output['Renamer'],
                                mode = 'markers',
                                marker_color = 'darkorange', 
                                marker_size = 10,
                                name = (select_year-1)))
        
        # Add Lines
        for i in range(0, len(syd)):
                    fig3.add_shape(type='line',
                                    x0 = syd[i],
                                    y0 = i,
                                    x1 = sydm1[i],
                                    y1 = i,
                                    line=dict(color='crimson', width = 3))
        
        # Update Layout
        fig3 = fig3.update_layout(height=400,legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=10,b=10))
        
        st.plotly_chart(fig3,use_containter_width=True)
        
        filtered_output = filtered_output.sort_values(by=['Delta'],ascending=False)

        # Convert Column names to string for AgGrid
        filtered_output.columns = filtered_output.columns.astype(str)

        AgGrid_default(filtered_output)
        
    else:

        type = st.radio("View List of",['New','Increased','Lost','Decreased'], horizontal=True)

        if type=='New':
        
            st.subheader(f'New donors in {select_year}')
            tmp = output[(output[select_year]>0) & (output[(select_year-1)]==0)]
            tmp.columns = tmp.columns.astype(str)
            AgGrid_default(tmp)
        
        elif type=='Increased':
        
            st.subheader(f'Increased donors in {select_year}')
            tmp = output[(output['Delta']>0) & (output[(select_year-1)]!=0)]
            tmp.columns = tmp.columns.astype(str)
            AgGrid_default(tmp)
        
        elif type=='Lost':
        
            st.subheader(f'Lost donors in {select_year}')
            tmp = output[(output[select_year]==0) & (output[(select_year-1)]>0)]
            tmp.columns = tmp.columns.astype(str)
            AgGrid_default(tmp)
        
        else:
        
            st.subheader(f'Decreased donors in {select_year}')
            tmp = output[(output['Delta']<0) & (output[(select_year-1)]!=0)]
            tmp.columns = tmp.columns.astype(str)
            AgGrid_default(tmp)
        
st.set_page_config(page_title="Donor Comparison", page_icon="📊",layout='centered')

st.title('Donor Comparison')

if 'password_check' in st.session_state:
    dc_page()
else:
    st.subheader('Error: Go to Home to enter Password')