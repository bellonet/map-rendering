import pyvista as pv
import numpy as np
import netCDF4 as nc
import gemgis as gg
import pandas as pd


def format_date(date):
    date = str(date)
    return f'{date[6:8]}/{date[4:6]}/{date[:4]}'



def try_create_mesh(arr, fill_value):

    min_val = np.min(arr)

    n_points = 0
    z_min_bound = fill_value
    ## due to sometimes producing an empty / incorrect mesh:
    ## while I catch the error from `unstructured_grid` the error already happens when creating`grid`
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

    return  grid



def create_timepoint_surface(ds, heat_arr_name, fill_value, tp_idx, n_smooth_itr):

    arr = ds[heat_arr_name][tp_idx]
    grid = try_create_mesh(arr, fill_value)

    # creates a pyvista.PolyData -  needed for smoothening and uses less memory
    surface = grid.extract_geometry()

    # smooth the surface:
    if n_smooth_itr:        
        surface = surface.smooth(n_iter=n_smooth_itr)

    return surface



def run_render(dataset_path, output_path, n_timepoints, n_smooth_itr, event_csv, opacity, framerate):

    # dataset:
    ## preprocessing steps:
    heat_arr_name = 'surface_upward_sensible_heat_flux' # check with dataset has 3D and get name??
    ds = nc.Dataset(dataset_path)
    time_arr = ds['time'][:]
    long_arr = ds['longitude'][:]
    lat_arr = ds['latitude'][:]
    fill_value=-999

    # plotting params:
    cmap = 'seismic'
    clim = [-200, 200] # check values outside of range
    sargs = {"color":"black"} # scale bar arguments

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

    ### for event annotations on the dataset:
    ## create a csv file with this data.
    ## For now just shows a test example:
    points = np.array([[200., 200., 150.],])
    labels = [f'lorem ipsum \n lorem ipsum']

    actor_eventText = p.add_point_labels(points, labels, italic=True, font_size=20,
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
        
        if tp_idx==5:
            actor_eventText = p.add_point_labels(points, labels, italic=True, font_size=20,
                                shape_color='black', name='event_text',
                                point_color='green', point_size=20,
                                render_points_as_spheres=True,
                                always_visible=True, shadow=True)

        p.write_frame()
        
    pv.close_all()




run_render('/home/ella/work/heat_flux_anomalies/UFZ_RemoteSensing/HOLAPS-H-JJA_anomaly-d-2001-2005.nc',
    'test.mp4', 4, 10, None, 0.5, 5)