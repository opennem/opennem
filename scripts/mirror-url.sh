 wget -r -np -R "index.html*" --retry-connrefused -t5 --retry-on-http-error=403,501,503 --random-wait $@
