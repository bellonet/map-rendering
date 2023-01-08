import pyvista as pv
import numpy as np
import netCDF4 as nc
import gemgis as gg
import pandas as pd
import argparse

def get_events(event_csv_path, time_arr, long_arr, lat_arr):    
    ## for now also processing timepoints outside of user input timepoints.
    ## for now - not checking that long and lat values are close to values in arrays.
    ## e.g. [abs(long_arr[idx_long[i]]-val)<max_dist for i,val in enumerate(loc_arr[0])]

    event_dict = {}

    df = pd.read_csv(event_csv_path, dtype={"first_date":str, "last_date":str})
    ## add column - timepoint index of first and last date:
    for i in df.index:
        try:
            idx_first_date = time_arr.index(df.loc[i,"first_date"])
            idx_last_date = time_arr.index(df.loc[i,"last_date"])

            for idx in range(idx_first_date,idx_last_date+1):

                point = [(np.abs(long_arr-df.loc[i,"longitude"])).argmin(), 
                    (np.abs(lat_arr-df.loc[i,"latitude"])).argmin(), 
                    150] # x,y,z

                text = df.loc[i,'text']

                if str(idx) not in event_dict:
                    event_dict[str(idx)] = [[point], [text]]  
                else: 
                    event_dict[str(idx)][0].append(point)
                    event_dict[str(idx)][1].append(text) 

        except:
            print(f'WARNING: event csv has an invalid date - number {i}')

    return event_dict


def format_date(date):
    return f'{date[6:8]}/{date[4:6]}/{date[:4]}'



def try_create_mesh(arr, fill_value):

    min_val = np.min(arr)

    n_points = 0
    z_min_bound = fill_value
    ## due to sometimes producing an empty / incorrect mesh:
    ## while I catch the error from `unstructured_grid` the error already happens when creating`grid`
    i=0
    while not n_points or z_min_bound==fill_value:

        ## creates a pyvista.StructuredGrid
        grid = gg.visualization.create_dem_3d(dem=arr.filled(fill_value=fill_value), 
                                                  extent=[0,arr.shape[1],0,arr.shape[0]])
        #print(grid.actual_memory_size)
        grid.rename_array('Elevation','Heat')
        
        ## get rid of fill_val values:
        unstructured_grid = grid.threshold(int(min_val-2), invert=False, preference='point', all_scalars=True)
        n_points = unstructured_grid.n_points
        z_min_bound = unstructured_grid.bounds[4]
        if i==20:
            raise Exception("please rerun - mesh creation failed.")
        i+=1

    return unstructured_grid



def create_timepoint_surface(ds, heat_arr_name, fill_value, tp_idx, n_smooth_itr):

    arr = ds[heat_arr_name][tp_idx]
    grid = try_create_mesh(arr, fill_value)

    # creates a pyvista.PolyData -  needed for smoothening and uses less memory
    surface = grid.extract_geometry()

    # smooth the surface:
    if n_smooth_itr:        
        surface = surface.smooth(n_iter=n_smooth_itr)

    return surface



def run_render(dataset_path, output_path, n_timepoints, n_smooth_itr, opacity, framerate, event_csv_path):

    ds = nc.Dataset(dataset_path)
    # get the name of the heat array - the only one that is 3D:
    heat_arr_name = [k for k in ds.variables.keys() if len(ds[k].shape)==3][0]
    time_arr = [s[:-2] for s in (ds['time'][:]).astype(str)]
    long_arr = ds['longitude'][:]
    lat_arr = ds['latitude'][:]

    fill_value=-999

    # plotting params:
    cmap = 'seismic'
    clim = [-200, 200] # check values outside of range
    sargs = {"color":"black"} # scale bar arguments

    events_per_time_idx_dict = {}
    if event_csv_path!='None':
        events_per_time_idx_dict = get_events(event_csv_path, time_arr, long_arr, lat_arr)

    ## Create our render engine
    p = pv.Plotter(notebook=False, off_screen=True, 
                   window_size=[1920*2, 1080*2], multi_samples=16) # multi_sample mitigates aliasing - higher is better, but might affect performance.

    ## Open up an MP4 with a 60 FPS framerate
    p.open_movie(output_path, framerate=framerate)

    p.set_background('white')

    print(f'rendering time point: 0')

    actor_mesh = p.add_mesh(mesh=create_timepoint_surface(ds, heat_arr_name, fill_value, 0, n_smooth_itr), clim=clim, cmap=cmap, opacity=opacity, scalar_bar_args=sargs)
    actor_date = p.add_text(format_date(time_arr[0]), position='upper_right', color='blue', shadow=True, font_size=26)

    # Camera position is a tuple: camera location, focus point, viewup vector
    # [(x,y,z), (fx,fy,fz,), (nx,ny,nz)]

    p.camera_position = 'xy'
    p.camera.zoom(1.5)

    if '0' in events_per_time_idx_dict:
        actor_eventText = p.add_point_labels(events_per_time_idx_dict['0'][0],
                                            events_per_time_idx_dict['0'][1], 
                                            italic=True, font_size=20,
                                            shape_color='black', name='event_text',
                                            point_color='green', point_size=20,
                                            render_points_as_spheres=True,
                                            always_visible=True, shadow=True)

    p.show(auto_close=False)

    ## Run through each frame
    p.write_frame()  ## write initial data

    for tp_idx in range(1,n_timepoints):

        print(f'rendering time point: {tp_idx}')
        p.remove_actor(actor_mesh)
        p.remove_actor(actor_date)
        p.remove_actor('event_text')

        actor_mesh = p.add_mesh(mesh=create_timepoint_surface(ds, heat_arr_name, fill_value, tp_idx, n_smooth_itr), clim=clim, cmap=cmap, opacity=opacity, scalar_bar_args=sargs)
        actor_date = p.add_text(format_date(time_arr[tp_idx]), position='upper_right', color='blue', shadow=True, font_size=26)
        
        if str(tp_idx) in events_per_time_idx_dict:
            actor_eventText = p.add_point_labels(events_per_time_idx_dict[str(tp_idx)][0],
                                            events_per_time_idx_dict[str(tp_idx)][1], 
                                            italic=True, font_size=20,
                                            shape_color='black', name='event_text',
                                            point_color='green', point_size=20,
                                            render_points_as_spheres=True,
                                            always_visible=True, shadow=True)

        p.write_frame()
        
    pv.close_all()



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    parser.add_argument('--dataset_path', required=True)
    parser.add_argument('--output_path', default='output.mp4')
    parser.add_argument('--n_timepoints', default=10, type=int)
    parser.add_argument('--n_smooth_itr', default=0, type=int)
    parser.add_argument('--opacity', default=1, type=float)
    parser.add_argument('--framerate', default=20, type=int)
    parser.add_argument('--event_csv_path', default='None')

    args = parser.parse_args()

    run_render(args.dataset_path, args.output_path, args.n_timepoints, 
        args.n_smooth_itr, args.opacity, args.framerate, args.event_csv_path)