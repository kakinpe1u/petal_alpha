


class EmailAuthTokenGenerator(object):
    """
    This object is created for user email verification
    """

    def make_token(self, user, pleb):
        if pleb is None:
            return None
        return self._make_timestamp_token(user, self._num_days(self._today()),
                                          pleb)

    def check_token(self, user, token, pleb):
        if token is None:
            return False
        try:
            timestamp_base36, hash_key = token.split("-")
        except ValueError:
            return False

        try:
            timestamp = base36_to_int(timestamp_base36)
        except ValueError:
            return False

        if not constant_time_compare(self._make_timestamp_token(
                user, timestamp, pleb), token):
            return False

        if (self._num_days(self._today()) - timestamp) > \
                settings.EMAIL_VERIFICATION_TIMEOUT_DAYS:
            return False

        return True