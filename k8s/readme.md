# Sal on Kubernetes

## Resources


## Secrets

The provided resource definitions reference secrets that must be added to the Kubernetes cluster before the associated pods can start.

The resource definitions ensure that the secrets are loaded as environment variables (or mounted to the filesystem in the case of the TLS certificate and private key. If the secrets are not defined, containers will not start.

### Creating Secrets

The recommended method for creating secrets is to save the secret values into files, and then create the secret resources using the `kubectl create secret` command.
