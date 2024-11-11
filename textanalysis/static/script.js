$(document).ready(function() {
    $('#upload-form').on('submit', function(event) {
        event.preventDefault(); // Prevent the form from submitting the traditional way

        var formData = new FormData(this);

        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#extracted-text').text(response.text);
                $('#results').show();
                if (response.entities.length > 0) {
                    $('#view-entities-btn').show().on('click', function() {
                        // Redirect to the page showing detected entities
                        window.location.href = "{% url 'detected_entities' %}";
                    });
                } else {
                    $('#view-entities-btn').hide();
                }
            },
            error: function(xhr, status, error) {
                alert('Error: ' + error);
            }
        });
    });
});



