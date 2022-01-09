# gcesync
This small script downloads gpx files from Garmin using [garmin-connect-export](https://github.com/pe-st/garmin-connect-export), and saves them in a directory. When you run it again, it will only download new gpx files.

## Directory structure of synced gpxfiles

```
/root
    |-/Walking
    |   |-<yyyy-mm-dd>_Walking-<location>.gpx
    |   |-<yyyy-mm-dd>_Walking-<location>.gpx
    |   |-<yyyy-mm-dd>_Walking-<location>.gpx
    |
    |-/Cycling
    |   |-<yyyy-mm-dd>_Cycling-<location>.gpx
    |   |-<yyyy-mm-dd>_Cycling-<location>.gpx
    |   |-<yyyy-mm-dd>_Cycling-<location>.gpx
    |
    |-/etc...
```

## Typical use
Run this script every week using cron to keep an offline copy of the gpx files.

## How to use
First, download [garmin-connect-export](https://github.com/pe-st/garmin-connect-export). Then, make a `settings.json` file, following the example given in `settings.json.example`:

 * The `gce_location` option needs the path to the directory you downloaded `garmin-connect-export` to, either relative to your working directory or absolute. 
 * `username` and `password` are your credentials for Garmin.
 * `maxdownloads` is the maximum number of activities `garmin-connect-export` can download, you can probably just set this to a very high number, but it may be good to first test your settings with a small number.
 * `gpxtrack_folder` is the directory your gpx files will be synced to.
 * By default, this script will scan the existing files to get the _Garmin ID_ of each gpx file. This ID is used to determine whether a file should be downloaded. By setting `use_persistent_garminidlist` to `True`, you can change the behaviour and make use of the list of ids (location set by `persistent_garminids` option) this script outputs after every run. This is faster because we don't scan all files every run, but it requires you to keep this list of ids around, which can be annoying.

Next, just run `python gcesync` (with settings in the working directory) to sync giles.


