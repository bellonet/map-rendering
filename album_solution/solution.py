from album.runner.api import setup

# Please import additional modules at the beginning of your method declarations.
# More information: https://docs.album.solutions/en/latest/solution-development/

env_file = """channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pyvista=0.37.0
  - netCDF4=1.6.2
  - vtk=9.2.2
  - scipy=1.9.3
  - numpy=1.24.0
  - gemgis=1.0.0
  - imageio=2.23.0
  - imageio-ffmpeg=0.4.7
"""



def run():
    from album.runner.api import get_args
    args = get_args()
    # print("Hi", str(args.name), "nice to meet you!")

    #import time
    import pyvista as pv
    import numpy as np
    import netCDF4 as nc
    import gemgis as gg

    ### args:
    dataset_path = str(args.dataset_path)
    ####'/home/ella/work/heat_flux_anomalies/UFZ_RemoteSensing/HOLAPS-H-JJA_anomaly-d-2001-2005.nc'
    output_path = str(args.output_path)
    n_timepoints = int(args.n_timepoints)
    n_smooth_itr = int(args.n_smooth_itr)

    ## plot args:
    opacity=float(args.opacity)
    framerate=int(args.framerate)
    cmap = 'seismic'
    clim = [-200, 200]

    print(f'\nargs: \ndataset_path:{dataset_path} \noutput_path:{output_path} \nn_timepoints:{n_timepoints} \nsmooth_itr:{n_smooth_itr} \nopacity:{opacity} \nframerate:{framerate}')

    heat_var = 'surface_upward_sensible_heat_flux'
    fill_value=-999
    ds = nc.Dataset(dataset_path)
    arr_shape = ds.variables[heat_var].shape
    time_arr = ds['time'][:]

    def create_timepoint_mesh(ii):

        arr = ds[heat_var][ii]
        min_val = np.min(arr)

        ## due to sometimes producing an empty / incorrect mesh:
        n_points = 0
        z_min_bound = fill_value
        while not n_points or z_min_bound==fill_value:

            ## creates a pyvista.StructuredGrid
            grid = gg.visualization.create_dem_3d(dem=arr.filled(fill_value=fill_value), 
                                                  extent=[0,arr_shape[2],0,arr_shape[1]])
            
            grid.rename_array('Elevation','Heat')

            ## get rid of fill_val values:
            unstructured_grid = grid.threshold(int(min_val-2), invert=False, preference='point', all_scalars=True)
            n_points = unstructured_grid.n_points
            z_min_bound = unstructured_grid.bounds[4]

        grid = unstructured_grid

        ## smooth the surface:
        if n_smooth_itr:        
            # creates a pyvista.PolyData (surface data)
            grid = grid.extract_geometry()
            # Smooth the surface
            grid = grid.smooth(n_iter=n_smooth_itr)

        return grid

    sargs = {"color":"black"}

    # initialize the point cloud
    #update_pc(0)

    ## Create our render engine
    p = pv.Plotter(notebook=False, off_screen=True, 
                   window_size=[1920*2, 1080*2], multi_samples=16) # multi_sample mitigates aliasing - higher is better, but might affect performance.

    ## Open up an MP4 with a 60 FPS framerate
    p.open_movie(output_path, framerate=framerate)

    p.set_background('white')

    print(f'rendering time point: 0')

    actor_mesh = p.add_mesh(mesh=create_timepoint_mesh(0), clim=clim, cmap=cmap, opacity=opacity, scalar_bar_args=sargs)
    actor_timestamp = p.add_text(f'time stamp: {int(time_arr[0])}', position='upper_right', color='blue', shadow=True, font_size=26)

    # Camera position is a tuple: camera location, focus point, viewup vector
    # [(x,y,z), (fx,fy,fz,), (nx,ny,nz)]

    p.camera_position = 'xy'
    p.camera.zoom(1.5)

    ### for event annotations on the dataset:
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

    for i in range(1,n_timepoints):

        print(f'rendering time point: {i}')
        p.remove_actor(actor_mesh)
        p.remove_actor(actor_timestamp)
        p.remove_actor('event_text')

        actor_mesh = p.add_mesh(mesh=create_timepoint_mesh(i), clim=clim, cmap=cmap, opacity=opacity, scalar_bar_args=sargs)
        actor_timestamp = p.add_text(f'time stamp: {int(time_arr[i])}', position='upper_right', color='blue', shadow=True, font_size=26)
        
        if i==5:
            actor_eventText = p.add_point_labels(points, labels, italic=True, font_size=20,
                                shape_color='black', name='event_text',
                                point_color='green', point_size=20,
                                render_points_as_spheres=True,
                                always_visible=True, shadow=True)

        p.write_frame()
        
    pv.close_all()


setup(
    group="album",
    name="netCDF_heatflux_pyvista_render",
    version="0.1.0",
    title="netCDF heatflux pyvista render",
    description="create a video of rendered (pyvista) sequential time points of netCDF heat-flux data.",
    #authors=["Album team - Ella"],
    cite=[],
    tags=["netCDF", "pyvista", "render", "python"],
    license="unlicense",
    #documentation=["documentation.md"], ### MISSING!!
    covers=[{
        "description": "render timepint example",
        "source": "cover.png"
    }],
    album_api_version="0.5.1",
    args=[{
        "name": "dataset_path",
        "type": "string",
    ##     "default": "dataset.nc",
        "description": "full path to the netCDF dataset"
        },
        {
        "name": "output_path",
        "type": "string",
        "default": "nc_movie.mp4",
        "description": "path to the output movie - should end with .mp4"
        },
        {
        "name": "n_timepoints",
        "type": "integer",
        "default": 10,
        "description": "number of timepoints to be rendered (starting from first time point)"
        },
        {
        "name": "n_smooth_itr",
        "type": "integer",
        "default": 0,
        "description": "number of mesh smoothening iterations - recommended as multiplications of 50. Warning: slower run!!"
        },
        {
        "name": "opacity",
        "type": "float",
        "default": 1.0,
        "description": "Mesh opacity"
        },
        {
        "name": "framerate",
        "type": "integer",
        "default": 5,
        "description": "video framerate (frames per second)."
        },],
    run=run,
    dependencies={'environment_file': env_file}
)
