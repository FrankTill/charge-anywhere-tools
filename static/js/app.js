document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("changeCountryForm");
  const submitBtn = document.getElementById("submitBtn");
  const results = document.getElementById("results");
  const resultContent = document.getElementById("resultContent");
  const errorSection = document.getElementById("errorSection");
  const errorContent = document.getElementById("errorContent");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    // Hide previous results
    results.classList.add("d-none");
    errorSection.classList.add("d-none");

    // Show loading state - just change text, no spinner
    submitBtn.disabled = true;
    // Since we removed the spinner, the text is now childNodes[0]
    const textNode = submitBtn.childNodes[0];
    textNode.textContent = "Processing...";

    const formData = new FormData(form);
    const data = {
      merchant_id: formData.get("merchant_id"),
      terminal_id: formData.get("terminal_id"),
      country: formData.get("country"),
    };

    try {
      const response = await fetch("/update_country", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams(data),
      });

      const result = await response.json();

      if (result.success) {
        // Show success response
        const isSuccess = result.is_success;
        const alertClass = isSuccess ? "alert-success" : "alert-warning";

        resultContent.innerHTML = `
                    <div class="${alertClass}">
                        <h6>Merchant ID: ${result.merchant_id}</h6>
                        <h6>Terminal ID: ${result.terminal_id}</h6>
                        <h6>Country: ${result.country}</h6>
                        <hr>
                        <p><strong>Response Code:</strong> ${
                          result.response_code
                        }</p>
                        <p><strong>Response Text:</strong> ${
                          result.response_text
                        }</p>
                        ${
                          result.batch_closed
                            ? "<p><strong>Batch Status:</strong> Successfully closed before retry</p>"
                            : ""
                        }
                        ${
                          result.batch_close_error
                            ? "<p><strong>Batch Close Error:</strong> " +
                              result.batch_close_error +
                              "</p>"
                            : ""
                        }
                    </div>
                `;
        results.classList.remove("d-none");
      } else {
        // Show error
        errorContent.innerHTML = `
                    <p>${result.error}</p>
                `;
        errorSection.classList.remove("d-none");
      }
    } catch (error) {
      errorContent.innerHTML = `
                <p>Network error: ${error.message}</p>
            `;
      errorSection.classList.remove("d-none");
    } finally {
      // Reset button state - just change text back
      submitBtn.disabled = false;
      textNode.textContent = "Change Country";
    }
  });

  // Form validation
  const merchantIdInput = document.getElementById("merchant_id");
  const terminalIdInput = document.getElementById("terminal_id");
  const countrySelect = document.getElementById("country");

  function validateForm() {
    const merchantId = merchantIdInput.value.trim();
    const terminalId = terminalIdInput.value.trim();
    const country = countrySelect.value;

    const isValid =
      merchantId.length > 0 && terminalId.length > 0 && country.length > 0;
    submitBtn.disabled = !isValid;
  }

  merchantIdInput.addEventListener("input", validateForm);
  terminalIdInput.addEventListener("input", validateForm);
  countrySelect.addEventListener("change", validateForm);

  // Initial validation
  validateForm();
});
