FMI Weather Radar Safety Monitor
================================

A script to download radar imagery from Finnish Meteorological
Institute API and determine if there is rain close to Komakallio
observatory.

Copy `config.ini.example` to `config.ini` and replace placeholder
API key in the configuration file with a real API key from FMI. You
can acquire an API key from the [FMI website](https://ilmatieteenlaitos.fi/rekisteroityminen-avoimen-datan-kayttajaksi).

You can now run the script by calling `python radarsafety.py`