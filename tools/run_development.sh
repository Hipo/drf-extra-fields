docker build -t drf_extra_fields .
docker run -v $(pwd):/app -it drf_extra_fields /bin/bash