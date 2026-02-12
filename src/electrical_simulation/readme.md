* Installing PySpice and NgSpice for electonic circuit simulation

```bash
pip install pyspice

pyspice-post-installation --install-ngspice-dll

pyspice-post-installation --check-install
```

* Note:

Spice identifier name should not start with number or 'v'

- Number used to indicate array index for MPPT and solar panels
- v prefix added by ngspice removed for result output
