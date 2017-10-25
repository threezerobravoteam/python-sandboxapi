import time
import random

import requests


__all__ = [
    'cuckoo',
    'fireeye',
    'joe',
    'vmray',
    'vxstream',
]


class SandboxError(Exception):
    """
    Custom exception class to be raised by known errors in SandboxAPI and its
    subclasses, and caught where this library is used.
    """
    pass


class SandboxAPI(object):
    """Sandbox API wrapper base class"""

    def __init__(self, *args, **kwargs):
        """Initialize the interface to Sandbox API"""

        self.api_url = None

        # assume is *not* available.
        self.server_available = False

        # turn SSL verify on by default
        self.verify_ssl = True

    def _request(self, uri, method='GET', params=None, files=None, headers=None, auth=None):
        """Robustness wrapper. Tries up to 3 times to dance with the Sandbox API.

        @type  uri:    str
        @param uri:    URI to append to base_url.
        @type  params: dict
        @param params: Optional parameters for API.
        @type  files:  dict
        @param files:  Optional dictionary of files for multipart post.

        @rtype:  requests.response.
        @return: Response object.

        @raise SandboxError: If all attempts failed.
        """

        # make up to three attempts to dance with the API, use a jittered
        # exponential back-off delay
        for i in xrange(3):
            try:
                full_url = '{b}{u}'.format(b=self.api_url, u=uri)

                response = None
                if method == 'POST':
                    response = requests.post(full_url, data=params, files=files, headers=headers,
                                             verify=self.verify_ssl, auth=auth)
                else:
                    response = requests.get(full_url, params=params, headers=headers,
                                            verify=self.verify_ssl, auth=auth)

                # if the status code is 503, is no longer available.
                if response:
                    if response.status_code >= 500:
                        # server error
                        self.server_available = False
                        raise SandboxError("server returned {c} status code on {u}, assuming unavailable...".format(
                            c=response.status_code, u=response.url))
                    else:
                        return response

            # 0.4, 1.6, 6.4, 25.6, ...
            except requests.exceptions.RequestException:
                time.sleep(random.uniform(0, 4 ** i * 100 / 1000.0))

        # if we couldn't reach the API, we assume that the box is down and lower availability flag.
        self.server_available = False

        # raise an exception.
        msg = "exceeded 3 attempts with sandbox API: {u}, p:{p}, f:{f}".format(u=full_url,
                                                                               p=params, f=files)
        msg += "\n" + response.content

        raise SandboxError(msg)

    def analyses(self):
        """Retrieve a list of analyzed samples.

        @rtype:  list
        @return: List of objects referencing each analyzed file.
        """
        raise NotImplementedError

    def analyze(self, handle):
        """Submit a file for analysis.

        @type  handle:   File handle
        @param handle:   Handle to file to upload for analysis.

        @rtype:  str
        @return: Task ID as a string
        """
        raise NotImplementedError

    def check(self, task_id):
        """Check if an analysis is complete

        @type  task_id: int | str
        @param task_id: task_id to check.

        @rtype:  bool
        @return: Boolean indicating if a report is done or not.
        """
        raise NotImplementedError

    def delete(self, task_id):
        """Delete the reports associated with the given task_id.

        @type  task_id: int | str
        @param task_id: Report ID to delete.

        @rtype:  bool
        @return: True on success, False otherwise.
        """
        raise NotImplementedError

    def is_available(self):
        """Determine if the Sandbox API servers are alive or in maintenance mode.

        @rtype:  bool
        @return: True if service is available, False otherwise.
        """
        raise NotImplementedError

    def queue_size(self):
        """Determine sandbox queue length

        @rtype:  int
        @return: Number of submissions in sandbox queue.
        """
        raise NotImplementedError

    def report(self, task_id, **kwargs):
        """Retrieves the specified report for the analyzed item, referenced by task_id.

        @type  task_id: int | str
        @param task_id: Task ID

        @rtype:  dict
        @return: Dictionary representing the JSON parsed data or raw, for other
                 formats / JSON parsing failure.
        """
        raise NotImplementedError
