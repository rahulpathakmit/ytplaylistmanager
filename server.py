from flask import Flask, request
import json
import pymongo
import requests
from math import ceil
app = Flask(__name__)

client = pymongo.MongoClient("mongodb+srv://santin:yt1234@cluster0.tamwg.mongodb.net/YTMeta?retryWrites=true&w=majority")
db = client['YTMeta']

@app.route('/login')
def login():
    headers=request.headers
    response=requests.get("https://youtube.googleapis.com/youtube/v3/playlists?part=snippet%2CcontentDetails&maxResults=2&mine=true&key=AIzaSyCTTLu3QB2FCFwXdT_7wSR95AZJsPpRbZw", headers={'Authorization': "Bearer {}".format(headers['accessToken']), 'Accept': 'application/json'})
    results=response.json()

    total_results = results['pageInfo']['totalResults']
    results_token=results


    for i in range(0, ceil(total_results/2)):

        if 'nextPageToken' in results_token.keys():

            nextPageToken = results['nextPageToken']

            url="https://youtube.googleapis.com/youtube/v3/playlists?pageToken={}&part=snippet%2CcontentDetails&maxResults=25&mine=true&key=AIzaSyCTTLu3QB2FCFwXdT_7wSR95AZJsPpRbZw".format(nextPageToken)

            response = requests.get(url, headers={'Authorization': "Bearer {}".format(headers['accessToken']), 'Accept': 'application/json'})

            results_token = response.json()
            results['items'].extend(results_token['items'])

        else:
            break
    playlists=[]
    playlistItems=[]
    deleted_videos=[]
    for i in range (results['pageInfo']['totalResults']):
        url="https://youtube.googleapis.com/youtube/v3/playlistItems?part=status%2CcontentDetails%2Csnippet&maxResults=2&playlistId={}&key=AIzaSyCTTLu3QB2FCFwXdT_7wSR95AZJsPpRbZw".format(results['items'][i]['id'])
        response=requests.get(url, headers={'Authorization': "Bearer {}".format(headers['accessToken']), 'Accept': 'application/json'})
        results_playlistItems=response.json()
        playlistItems=results_playlistItems['items']
        total_results = results_playlistItems['pageInfo']['totalResults']
        results_playlistItems_token=results_playlistItems

        for j in range(0, ceil(total_results/2)):

            if 'nextPageToken' in results_playlistItems_token.keys():

                nextPageToken = results_playlistItems_token['nextPageToken']
                url="https://youtube.googleapis.com/youtube/v3/playlistItems?part=status%2CcontentDetails%2Csnippet&maxResults=2&playlistId={}&key=AIzaSyCTTLu3QB2FCFwXdT_7wSR95AZJsPpRbZw&pageToken={}".format(results['items'][i]['id'],nextPageToken)
                response = requests.get(url, headers={'Authorization': "Bearer {}".format(headers['accessToken']), 'Accept': 'application/json'})

                results_playlistItems_token = response.json()


                playlistItems.extend(results_playlistItems_token['items'])
                for item in results_playlistItems_token['items']:
                    title=item["snippet"]["title"]
                    videoId=item["contentDetails"]["videoId"]
                    privacyStatus=item["status"]["privacyStatus"]
                    if(title=="Deleted video" and privacyStatus=='privacyStatusUnspecified'):
                        deleted_videos.append(videoId)
            else:
                break
        playlists.append({'playlistId':results['items'][i]['id'], 'title':results['items'][i]['snippet']['title'], 'items': playlistItems})
    user_info={'name':headers['name'], 'email':headers['email'], 'playlists':playlists}
    if db['users'].count_documents({ 'email': headers['email'] }, limit = 1) > 0:
        info = db['users'].find({'email':headers['email']})
        user=(info[0])
        del user['_id']
        for playlist in user['playlists']:
            for item in playlist['items']:
                videoId=item["contentDetails"]["videoId"]
                if videoId in deleted_videos:
                    item['status']['privacyStatus']='deleted'
        db['users'].update_one({'email':headers['email']}, {"$set":{'playlists': user['playlists']}})

        #for playlist in playlists:
         #   if playlist['playlistId'] not in user['playlists']:
          #      user['playlists'].append(playlist)

        return({'userInfo': user})
    else:

        db['users'].insert_one(user_info)
        return({'msg':user_info})

@app.route('/check')
def check():
    headers=request.headers
    url="https://youtube.googleapis.com/youtube/v3/playlistItems?part=status%2CcontentDetails%2Csnippet&maxResults=25&playlistId={}&key=AIzaSyCTTLu3QB2FCFwXdT_7wSR95AZJsPpRbZw".format(headers['playlistId'])
    response=requests.get(url, headers={'Authorization': "Bearer {}".format(headers['accessToken']), 'Accept': 'application/json'})
    results=response.json()
    playlistItemsAPI=results['items']
    user_info = db['users'].find({'email':headers['email']})
    info=user_info[0]
    del info['_id']
    playlist_info=(next(playlist for playlist in info['playlists'] if playlist["playlistId"] == headers['playlistId']))
    playlistItemsDB=playlist_info['items']

    deleted_videoId=[]
    for item in playlistItemsAPI:
        title=item["snippet"]["title"]
        videoId=item["contentDetails"]["videoId"]
        privacyStatus=item["status"]["privacyStatus"]
        if(title=="Deleted video" and privacyStatus=='privacyStatusUnspecified'):
            deleted_videoId.append(videoId)
    vids=[]
    for video_id in deleted_videoId:
        for video in playlistItemsDB:
            if(video_id==video['contentDetails']['videoId']):
                vids.append(video['snippet']['title'])
    
    return({'deletedVid':vids})
