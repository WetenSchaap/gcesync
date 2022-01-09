import json
import sys
import pandas as pd
import tempfile
import os
import os.path
import glob
import shutil
import tempfile
import xml.dom
import xml.dom.minidom

def add_garminID_gpx(gpxfile,garminID):
    """
    Add garmin ID to a gpx file at the metadata tag.
    """
    tf = xml.dom.minidom.parse( gpxfile )
    gpx = tf.getElementsByTagName( "gpx" )[0]
    metadata = gpx.getElementsByTagName( "metadata" )[0]
    metadata.setAttribute("GarminID", str(garminID) )
    with open(gpxfile,"w") as f:
        tf.writexml(f)

def get_garminID_gpx(gpxfile):
    """
    Get GarminID from GPX file. If there is no GarminID, will return an empty string.
    """
    tf = xml.dom.minidom.parse( gpxfile )
    gpx = tf.getElementsByTagName("gpx")[0]
    metadata = gpx.getElementsByTagName("metadata")[0]
    garminID = metadata.getAttribute("GarminID") # wil be '' if garminID does not exist.
    return garminID

def collect_existing_garminID(gpxtrackdir):
    """
    Get all GarminIDs from the gpx files in the gpxtrackdir directory and all its subdirectories. Returns a list of IDs.
    """
    all_gpxs = [f for f in glob.glob(os.path.join(gpxtrackdir,'**/*.gpx'), recursive=True)]
    ids = list()
    for gpx in all_gpxs:
        garminid = get_garminID_gpx(gpx)
        if garminid != '': # in case garmin is not the source of the gpx file.
            ids.append( str( garminid ) )
    return ids

# hardcoded settings
setting_file = r"./settings.json"
tracksubdir = "tracks"

print("Load settings")
with open(setting_file,"r") as f:
    settings = json.load(f)
gpxtrack_folder = settings["gpxtrack_folder"]
persistent_ids = settings["persistent_garminids"]
if not os.path.exists(gpxtrack_folder):
        raise FileNotFoundError("In your settings file, 'gpxtrack_folder' is set to a non-existing path. Set it to the correct directory, or create an empty directory.")

print("Load garmin-connect-export")
gcepath = os.path.abspath(settings["gce_location"])
sys.path.append(gcepath)
import gcexport

# load GarminIDs of previously downloaded tracks
if settings["use_persistent_garminidlist"]:
    print("Load GarminIDs from persistent storage")
    if not os.path.exists(persistent_ids):
        raise FileNotFoundError("In your settings file, 'persistent_garminids' is set to a non-existing file. Change it to an existing file, or set use_persistent_garminidlist to generate the file.")
    with open(persistent_ids,"r") as f:
        id_dict = json.load(f)
else:
    print("Check existing gpx files for GarminIDs")
    ids = collect_existing_garminID(gpxtrack_folder)
    id_dict = {"ids" : ids}
    with open(persistent_ids,"w") as f:
        json.dump(id_dict,f,indent="\t")

id_list = id_dict["ids"]
# shutil.copy2(persistent_ids,persistent_ids+".backup") # just for testing.

print("Start garmin-connect-export:")
with tempfile.TemporaryDirectory() as downloaddir:
    # passing my commands to gcexport without going through the commandline, see https://stackoverflow.com/questions/47021142/python-simulate-sys-argv-when-calling-script-as-function-without-modifying-it
    command_line_arguments = [
        "garmin-connect-export", # basically a dummy entry...
        "--username", settings["username"],
        "--password", settings["password"],
        "--count", settings["maxdownloads"],
        "--format", "gpx", # might make this a setting at some point
        "--directory", downloaddir,
        "--subdir", tracksubdir,
        "--exclude", persistent_ids,
        "--originaltime"
    ]
    gcexport.main( command_line_arguments )

    # Now, we want to see what files we have, fortunately there is a csv file with the data I need
    print("Now handling downloaded GPXfiles")
    gpxfiles = glob.glob( os.path.join(downloaddir, tracksubdir,"*.gpx") )
    activities = pd.read_csv( os.path.join(downloaddir, "activities.csv") )

    for idx, row in activities.iterrows():
        gpx_downloaded = [i for i in gpxfiles if (str(row["Activity ID"]) in i)][0]
        add_garminID_gpx(gpx_downloaded,str(row["Activity ID"]))
        activity_type = row["Activity Type"]
        save_name = "{0}_{1}.gpx".format( row["Start Time"][:10], row["Activity Name"].replace(' ', '-').lower() )
        if not os.path.isdir( os.path.join( gpxtrack_folder, activity_type ) ):
            os.mkdir( os.path.join( gpxtrack_folder, activity_type ) )
        gpx_new = os.path.join( gpxtrack_folder, activity_type, save_name )
        # check if gpx_new allready exists (can happen if multiple activities of the same type occur at the same place at the same day), and if it does, add an index.
        filename, extension = os.path.splitext(gpx_new)
        counter = 1
        while os.path.exists( gpx_new ):
            # gpx_new = filename + " (" + str(counter) + ")" + extension
            gpx_new = "{0}_{1}{2}".format(filename,counter,extension)
            counter += 1

        shutil.copy2(
            gpx_downloaded,
            gpx_new
        )
        # Okay done! Now, save the id of this file so I don't download it again
        id_list.append( str( row["Activity ID"] ) )

print("Add Garmin IDs to persistent storage.")
id_dict["ids"] = id_list
with open(persistent_ids,"w") as f:
    json.dump(id_dict,f,indent="\t")

print("Complete! Shutting down.")