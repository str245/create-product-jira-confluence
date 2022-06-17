import boto3
import logging


class HelperException(Exception):
    def __init__(self, helper_name, msg):
        super(HelperException, self).__init__(
            "An exception occurred inside helper: " + helper_name +
            " Error message: " + msg)


class SecretHelper:
    def __init__(self, client=None):
        if client is not None:
            self.client = client
        else:
            session = boto3.session.Session()
            self.client = session.client("ssm")

    def get_secret(self, secret, with_decryption=False):
        """
        Get the value of a secret from the parameter store.

        :param secret (string) : the name of the secret
        :param with_decryption (bool) : true if the parameter must be decrypted

        :return: The value of the secret
        """
        logging.info("Get secret[%s]" % secret)
        try:
            response = self.client.get_parameter(
                Name=secret,
                WithDecryption=with_decryption
            )
            logging.info("Got secret[%s]" % secret)

            if response and 'Parameter' in response \
                    and 'Value' in response['Parameter']:
                return response['Parameter']['Value']
            else:
                raise HelperException(
                    __class__.__name__,
                    "Error getting secret[%s]: not found" % secret)
        except Exception as err:
            print("EXCEPTION__")
            print(err)
            raise HelperException(
                __class__.__name__,
                "Error getting secret[%s]" % secret)

    def put_secret(self, secret, value, tags=[]):
        """
        Puts a secret to the store.

        :param secret (string) : the name of the secret
        :param value (bool) : the value of the secret

        :return:
        """
        if not secret:
            raise HelperException(
                __class__.__name__,
                "Error getting secret: invalid secret name")
        if not value:
            raise HelperException(
                __class__.__name__,
                "Error getting secret[%s]: invalid secret value" % secret)

        logging.info("Putting secret[%s]" % secret)
        try:
            self.client.put_parameter(
                Name=secret,
                Value=value,
                Type="SecureString"
            )

            logging.info("Put secret[%s]" % secret)
        except Exception:
            raise HelperException(
                __class__.__name__,
                "Error putting secret[%s]" % secret)
