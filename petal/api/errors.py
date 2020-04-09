from rest_framework import status

CYPHER_EXCEPTION = {
    "detail": "Error connecting to the database",
    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
}

QUERY_FILTER_EXCEPTION = {
    "detail": "We didn't understand that filter query.",
    "status": status.HTTP_400_BAD_REQUEST,
}

JSON_ERROR_EXCEPTION = {
    "detail": "We're having some difficulty with making some requests.",
    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
}

DOES_NOT_EXIST_EXCEPTION = {
    "detail": "This object does not exist.",
    "status": status.HTTP_404_NOT_FOUND,
}

CELERY_CONNECTION_ERROR = {
    "detail": "There's issue connecting to one of our services.",
    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
}

ELASTICSEARCH_NOT_FOUND_ERROR = {
    "detail": "We're having some problems with our search index. Please try again in a bit.",
    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,

}
