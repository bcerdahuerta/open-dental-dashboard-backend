import requests
import time
from requests.exceptions import RequestException, Timeout

class OpenDentalAPIError(Exception):
    """Custom exception for Open Dental API errors."""
    def __init__(self, status_code, message, response=None):
        super().__init__(f"OpenDentalAPIError {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.response = response

class OpenDentalAPI:
    """
    Open Dental API client.
    """
    def __init__(self, config, settings, logger=None, timeout=30):
        self.base_url = config["api"]["base_url"].rstrip("/")
        self.developer_key = config["api"]["developer_key"]
        self.customer_key = config["api"]["customer_key"]
        self.headers = self._build_headers()
        self.endpoints = settings["api"]["endpoints"]
        self.logger = logger
        self.timeout = timeout
        self._load_retry_settings(settings)

    def _build_headers(self):
        """Builds the authorization and content headers."""
        return {
            "Authorization": f"ODFHIR {self.developer_key}/{self.customer_key}",
            "Content-Type": "application/json"
        }

    def _load_retry_settings(self, settings):
        retry_cfg = settings["api"].get("retry", {})
        self.max_attempts = retry_cfg.get("max_attempts", 1)
        self.backoff_seconds = retry_cfg.get("backoff_seconds", 1)
        self.retry_on_statuses = retry_cfg.get("retry_on_statuses", [408, 429, 500, 502, 503, 504])

    def get(self, endpoint_name, path_vars=None, **kwargs):
        return self._request_with_retry("GET", endpoint_name, path_vars, **kwargs)

    def post(self, endpoint_name, path_vars=None, **kwargs):
        return self._request_with_retry("POST", endpoint_name, path_vars, **kwargs)

    def put(self, endpoint_name, path_vars=None, **kwargs):
        return self._request_with_retry("PUT", endpoint_name, path_vars, **kwargs)

    def delete(self, endpoint_name, path_vars=None, **kwargs):
        return self._request_with_retry("DELETE", endpoint_name, path_vars, **kwargs)

    def _request_with_retry(self, method, endpoint_name, path_vars=None, **kwargs):
        """Core HTTP request logic with retries."""
        url = self._build_url(endpoint_name, path_vars or {})
        req_headers = self.headers.copy()
        headers = kwargs.pop("headers", None)
        if headers:
            req_headers.update(headers)

        attempt = 0
        last_exc = None
        while attempt < self.max_attempts:
            attempt += 1
            try:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=req_headers,
                    timeout=self.timeout,
                    **kwargs
                )
                self._log_request(method, url, resp)
                if self._should_retry(resp, attempt):
                    self._wait_before_retry(attempt)
                    continue
                self._raise_if_error(resp)
                return self._parse_response(resp)
            except (Timeout, RequestException) as exc:
                last_exc = exc
                self._log_warning_retry(method, url, exc, attempt)
                if attempt >= self.max_attempts:
                    self._log_error(method, url, type(exc).__name__, exc)
                    raise OpenDentalAPIError(-1, f"Request failed after {self.max_attempts} attempts: {exc}") from exc
                self._wait_before_retry(attempt)

    def _should_retry(self, response, attempt):
        """Returns True if status is retryable and attempts remain."""
        return (response.status_code in self.retry_on_statuses and attempt < self.max_attempts)

    def _wait_before_retry(self, attempt):
        """Waits before the next retry attempt."""
        time.sleep(self.backoff_seconds)

    def _build_url(self, endpoint_name, path_vars):
        """Resolves endpoint path and interpolates variables."""
        if endpoint_name not in self.endpoints:
            raise ValueError(f"Endpoint '{endpoint_name}' not found in settings.yaml.")
        try:
            path = self.endpoints[endpoint_name].format(**path_vars)
        except KeyError as e:
            raise ValueError(f"Missing path variable: {e} for endpoint '{endpoint_name}'")
        return f"{self.base_url}/{path.lstrip('/')}"

    def _raise_if_error(self, response):
        if not response.ok:
            try:
                err_msg = response.json()
            except Exception:
                err_msg = response.text
            raise OpenDentalAPIError(response.status_code, err_msg, response=response)

    def _parse_response(self, response):
        if self._is_json(response):
            return response.json()
        return response.text

    def _is_json(self, response):
        ct = response.headers.get("Content-Type", "")
        return "application/json" in ct.lower()

    def _log_request(self, method, url, response):
        if self.logger:
            self.logger.info(
                f"OpenDentalAPI {method} {url} - Status {response.status_code}",
                extra_context={"response_preview": response.text[:300]},
                save_log=True
            )

    def _log_error(self, method, url, err_type, exc):
        if self.logger:
            self.logger.error(
                f"OpenDentalAPI {method} {url} - {err_type}: {exc}",
                extra_context={"exception": str(exc)},
                save_log=True
            )

    def _log_warning_retry(self, method, url, exc, attempt):
        if self.logger:
            self.logger.warning(
                f"OpenDentalAPI {method} {url} - {type(exc).__name__} on attempt {attempt}/{self.max_attempts}: {exc}", 
                save_log=True
            )

    def validate_auth(self):
        endpoint_name = "short_query"
        sql_body = {
            "SqlCommand": "SELECT programversion FROM updatehistory order by datetimeupdated desc"
        }
        response = self.put(endpoint_name, json=sql_body)
        if isinstance(response, dict) and response.get("Status") == "Error":
            raise OpenDentalAPIError(
                401, f"API Key not authorized or invalid: {response.get('ErrorMsg', 'Unknown error')}"
            )
        if self.logger:
            self.logger.info("OpenDentalAPI authentication validated successfully.")
        return True
