"""Basic I2C device classes for Raspberry PI & MicroPython"""

from meerkat import json_dumps


class Base:
    """Common methods"""

    def __repr__(self):
        return str(self.class_values())

    def class_values(self):
        """Get all class attributes from __dict__ attribute
        except those prefixed with underscore ('_') or
        those that are None (to reduce metadata size)

        Returns
        -------
        dict, of (attribute: value) pairs
        """
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            if k[0] == '_':
                continue
            d[k] = v
        return d

    def to_json(self, indent=None):
        """Return all class objects from __dict__ except
        those prefixed with underscore ('_')
        See self.class_values method for implementation.

        Returns
        -------
        str, JSON formatted (attribute: value) pairs
        """
        return json_dumps(self.class_values())
