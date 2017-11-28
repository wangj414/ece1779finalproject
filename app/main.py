from werkzeug.utils import redirect

from app import webapp
from flask import render_template, session, request, url_for

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


def get_table(table_name):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(table_name)
	return table

@webapp.route('/',methods=['GET'])
@webapp.route('/index', methods=['GET'])
def index():
	return render_template('index.html')


@webapp.route('/tea',methods=['GET'])
def bubble_tea_page():
    return render_template('bubbletea.html')


@webapp.route('/dessert',methods=['GET'])
def dessert_page():
    table = get_table('Desserts')
    response=table.scan()
    grid=[]
    description=[]
    count=0
    row=[]
    name=[]
    for i in response['Items']:
        #print(i['path'])
        if count==3:
            description.append(name)
            count=0
            grid.append(row)
            row=[]
            name=[]
        name.append(i['name']+": "+i['description'])
        row.append(i['path'])
        count+=1
    grid.append(row)
    description.append(name)
    #print(grid)
    #print(description)
    return render_template('dessert.html',grid=grid, description=description)


@webapp.route('/asian',methods=['GET'])
def asian_page():
    return render_template('asianfood.html')


@webapp.route('/french',methods=['GET'])
def french_page():
    return render_template('french.html')



@webapp.route('/detail',methods=['GET'])
def detail():
    path = request.args.get('info', "")
    table = get_table('Desserts')
    response = table.get_item(
        Key={
            'path': path,
        })

    # Display reviews
    temp = response['Item']
    reviews = temp['reviews']

    review_list=[]
    names=[]

    for key,value in reviews.items():
        names.append(key)
        review_list.append(value)

    temp = response['Item']
    description = temp['longdescription']

    email = session.pop("email", "")
    if email == "":
        return render_template('detail.html', path=path, liked=False, reviews=review_list, names=names, len=len(names),
                               description=description)
    session['email'] = email
    temp = response['Item']
    likes = temp['likes']
    if likes=={}:
        liked=False
    else:
        liked = likes[email]
    return render_template('detail.html', path=path, liked=liked, reviews=review_list, names=names, len=len(names), description=description)


@webapp.route('/detail/review',methods=['POST'])
def review():
    email = session.pop("email", "")
    if email == "":
        return render_template('dessert.html', err_msg=["You have to login to leave comment"])
    session['email'] = email
    review=request.form['review']
    path=request.form['path']

    table = get_table('Desserts')
    response = table.get_item(
        Key={
            'path': path,
        })

    temp = response['Item']
    reviews = temp['reviews']

    reviews[email]=review

    response2 = table.update_item(
        Key={
            'path': path,
        },
        UpdateExpression="set reviews = :a",
        ExpressionAttributeValues={
            ':a': reviews
        },
        ReturnValues="UPDATED_NEW"
    )
    return redirect('/detail?info='+path)


@webapp.route('/detail/favorite',methods=['POST'])
def favorite():
    favorite = request.form['button1']
    email = session.pop("email", "")
    if email == "":
        return render_template('favorites.html', err_msg=["You have to login to add favorites"])
    session['email'] = email
    print(email)

    table = get_table('UserInfo')

    response = table.get_item(
        Key={
            'email': email,
        })

    temp=response['Item']
    favorites = temp['favorites']
    favorites.append(favorite)

    response2 = table.update_item(
        Key={
            'email': email,
        },
        UpdateExpression="set favorites = :a",
        ExpressionAttributeValues={
            ':a': favorites
        },
        ReturnValues="UPDATED_NEW"
    )



    table0 = get_table('Desserts')
    response0 = table0.get_item(
        Key={
            'path': favorite,
        })
    temp0 = response0['Item']
    likes = temp0['likes']
    likes[email]=True

    response1 = table0.update_item(
        Key={
            'path': favorite,
        },
        UpdateExpression="set likes = :a",
        ExpressionAttributeValues={
            ':a': likes
        },
        ReturnValues="UPDATED_NEW"
    )


    return redirect(url_for('favorites'))



@webapp.route('/detail/disfavorite',methods=['POST'])
def disfavorite():
    disfavorite = request.form['button2']
    email = session.pop("email", "")
    if email == "":
        return render_template('favorites.html', err_msg=["You have to login to remove favorites"])
    session['email'] = email
    table = get_table('UserInfo')

    response = table.get_item(
        Key={
            'email': email,
        })

    temp=response['Item']
    favorites = temp['favorites']
    favorites.remove(disfavorite)

    response2 = table.update_item(
        Key={
            'email': email,
        },
        UpdateExpression="set favorites = :a",
        ExpressionAttributeValues={
            ':a': favorites
        },
        ReturnValues="UPDATED_NEW"
    )



    table0 = get_table('Desserts')
    response0 = table0.get_item(
        Key={
            'path': disfavorite,
        })
    temp0 = response0['Item']
    likes = temp0['likes']
    likes[email] = False

    response1 = table0.update_item(
        Key={
            'path': disfavorite,
        },
        UpdateExpression="set likes = :a",
        ExpressionAttributeValues={
            ':a': likes
        },
        ReturnValues="UPDATED_NEW"
    )

    return redirect(url_for('favorites'))



@webapp.route('/favorites',methods=['GET'])
def favorites():
    email = session.pop("email","")
    if email=="":
        return render_template('favorites.html')
    session['email']=email
    table = get_table('UserInfo')
    #print(email)
    response = table.get_item(
        Key={
            'email': email,
        })

    temp = response['Item']
    favorites = temp['favorites']

    fav_names=[]
    for i in range(len(favorites)):
        table0 = get_table('Desserts')

        response0 = table0.get_item(
            Key={
                'path': favorites[i],
            })
        temp0=response0['Item']
        fav_names.append(temp0['name']+": "+temp0['description'])
        #print(fav_names)
    grid = []
    count = 0
    row = []
    names=[]
    name=[]
    for i in range(len(favorites)):
        if count == 3:
            count = 0
            grid.append(row)
            names.append(name)
            row = []
            name=[]
        row.append(favorites[i])
        name.append(fav_names[i])
        count += 1
    grid.append(row)
    names.append(name)
    #print(grid)
    len1=len(grid)-1
    len2=len(grid[-1])
    #print(len1)
    #print(len2)
    return render_template('favorites.html', description=names ,grid=grid, len1=len1, len2=len2)








