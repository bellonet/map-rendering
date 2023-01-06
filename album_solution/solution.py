from album.runner.api import setup

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
    import render_movie_heatflux_timepoints

    args = get_args()
    ## call python.script

    ### args:
    dataset_path = str(args.dataset_path)
    ####'/home/ella/work/heat_flux_anomalies/UFZ_RemoteSensing/HOLAPS-H-JJA_anomaly-d-2001-2005.nc'
    output_path = str(args.output_path)
    n_timepoints = int(args.n_timepoints) ## change to range??
    n_smooth_itr = int(args.n_smooth_itr)
    event_csv = str(args.event_csv_path)

    ## plot args:
    opacity=float(args.opacity)
    framerate=int(args.framerate)

    # Print the arguments:
    print(f'\nargs: \ndataset_path:{dataset_path} \noutput_path:{output_path} \nn_timepoints:{n_timepoints} \nsmooth_itr:{n_smooth_itr} \nopacity:{opacity} \nframerate:{framerate}')

    render_movie_heatflux_timepoints.run_render(dataset_path, output_path, n_timepoints, n_smooth_itr, event_csv, opacity, framerate)

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
        },
        {
        "name": "event_csv_path",
        "type": "string",
        "default": None,
        "description": "csv with events to display on the map - columns: first date (e.g. 20001231), last date, latitude, longitude"
        },],
    run=run,
    dependencies={'environment_file': env_file}
)
