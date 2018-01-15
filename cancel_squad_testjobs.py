#!/usr/bin/env python3
import argparse
import json
import requests

from netrcauth import Auth
from proxy import LAVA
from pprint import pprint


def get_objects(endpoint_url, expect_one=False, parameters={}):
    """
    gets list of objects from endpoint_url
    optional parameters allow for filtering
    expect_count
    """
    obj_r = requests.get(endpoint_url, parameters)
    if obj_r.status_code == 200:
        objs = obj_r.json()
        if 'count' in objs.keys():
            if expect_one and objs['count'] == 1:
                return objs['results'][0]
            else:
                ret_obj = []
                while True:
                    for obj in objs['results']:
                        ret_obj.append(obj)
                    if objs['next'] is None:
                        break
                    else:
                        obj_r = requests.get(objs['next'])
                        if obj_r.status_code == 200:
                            objs = obj_r.json()
                return ret_obj
        else:
            return objs

def main():

    parser = argparse.ArgumentParser(description='Cancel LAVA jobs')
    parser.add_argument('--project-slug',
        dest='project_slug',
        required=True,
        help='slug of the project which test jobs will be canceled')
    parser.add_argument('--squad-url',
        dest='squad_url',
        required=True,
        help='URL of SQUAD instance in form https://example.com')
    parser.add_argument('--build-version',
        dest='build_version',
        required=True,
        help='Version of the build from which testjobs will be canceled')

    args = parser.parse_args()
    params={"slug": args.project_slug}
    base_url = args.qa_reports_url + "/api/projects/"

    project = get_objects(base_url, True, params)
    # can't search in versions through the API yet :(
    # this will be fixed by https://github.com/Linaro/squad/pull/208
    build_list = get_objects(project['builds'])
    for build in build_list:
        if build['version'] == args.build_version:
            testjobs = get_objects(build['testjobs'])
            for testjob in testjobs:
                backend = get_objects(testjob['backend'])
                print("Canceling: %s/scheduler/job/%s" % (backend['url'].replace("/RPC2/",""), testjob['job_id']))
                a = Auth(backend['url'])
                l = LAVA(backend['url'], a.username, a.token)
                c_results = l.proxy.scheduler.cancel_job(testjob['job_id'])
                pprint (c_results)

if __name__ == "__main__":
    main()
