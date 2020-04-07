from uuid import uuid1
from rest_framework.validators import UniqueValidator


def generate_job(job_func, job_param, countdown = 0, job_id = None):
    if job_id is None:
        job_id = str(uuid1())
    try:
        return job_func.apply_async(kwargs = job_param, countdown = countdown,
                                    job_id = job_id)
    except (IOError, Exception) as exception:

        failure_uuid = str(uuid1())
        failure_dict = {
            'action': 'failed_job',
            'attempted_job': job_func.__name__,
            'job_info_kwargs': job_param,
            'failure_uuid': failure_uuid
        }
        # add_failure_to_queue(failure_dict)
        raise exception

class PetalUniqueValidator(UniqueValidator):
    """
    Validator that corresponds to `unique=True` on a model field.
    Should be applied to an individual field on the serializer.
    """

    def exclude_current_instance(self, queryset):
        """
        If an instance is being updated, then do not include
        that instance itself as a uniqueness conflict.
        """
        if self.instance is not None:
            return queryset.exclude(username = self.instance.username)
        return queryset

def collect_request_data(context, expedite_param = None, expand_param = None):
    try:
        request = context['request']
        try:
            expand = request.query_params.get('expand', 'false').lower()
            expedite = request.query_params.get('expedite', "false").lower()
            relations = request.query_params.get(
                'relations', 'primaryKey').lower()
            html = request.query_params.get('html', 'false').lower()
            expand_array = request.query_params.get('expand_attrs', [])
            if html == 'true':
                expand = 'true'
        except AttributeError:
            try:
                expand = request.GET.get('expand', 'false').lower()
                expedite = request.GET.get('expedite', 'false').lower()
                relations = request.GET.get('relations', 'primaryKey').lower()
            except AttributeError:
                expand = 'false'
                expedite = 'false',
                relations = 'primaryKey'
                request = None
            expand_array = []
    except KeyError:
        expand = 'false'
        expedite = 'false'
        relations = "primaryKey"
        request = None
        expand_array = []

    if expedite_param is not None:
        expedite = 'true'
    if expand_param:
        expand = 'true'

    return request, expand, expand_array, relations, expedite
