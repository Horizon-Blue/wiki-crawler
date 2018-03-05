from flask_restful import Resource, abort
from flask import request
from database import db_session
from sqlalchemy import and_, or_, func
from model.graph import Actor, Edge, Movie, Graph
from .util import parse_query

GROSS_RANGE = 5000
graph = Graph(db_session)

def generate_query(queries):
    """
    A helper method to get the actor query from queries
    :param queries: the list of dictionary containing queries to filter query
    :return: query corresponding to queries
    """
    filters = []
    for query in queries:
        query_filter = []
        # check each field
        if "name" in query:
            query_filter.append(Actor.name.contains(query.get("name")))
        if "age" in query:
            try:
                query_filter.append(Actor.age == int(query.get("age")))
            except ValueError:
                ...  # skip this argument
        if "wiki_page" in query:
            query_filter.append(Actor.wiki_page.contains(query.get("name")))
        if "total_gross" in query:
            try:
                gross = float(query.get("total_gross"))
                query_filter.append(and_(Actor.total_gross >= gross - GROSS_RANGE,
                                         Actor.total_gross <= gross + GROSS_RANGE))
            except ValueError:
                ...  # skip this argument
        if "movie" in query or "movies" in query:
            movie_list = [query.get("movie")] if "movie" in query else query.get("movies").split(',')
            query_filter.append(and_(*[Actor.movies.any(Edge.movie.has(Movie.name.contains(movie_name.strip())))
                                       for movie_name in movie_list]))
        filters.append(and_(*query_filter))
    return or_(*filters)


class ActorQueryResource(Resource):
    """
    The Flask-Restful Resource class used for creating
    API for Actor query
    """

    def get(self):
        queries = parse_query(request.query_string.decode("utf-8"))
        return [actor.to_dict() for actor in Actor.query.filter(generate_query(queries)).all()]


class ActorResource(Resource):
    """
    The Flask-Restful Resource class used for creating
    API for a single Actor
    """

    def get(self, name):
        actor_name = name.replace("_", " ")
        actor = Actor.query.filter(func.lower(Actor.name) == func.lower(actor_name)).first()
        if actor is not None:
            return actor.to_dict()
        else:
            abort(404, message="Actor {} doesn't exist".format(actor_name))
