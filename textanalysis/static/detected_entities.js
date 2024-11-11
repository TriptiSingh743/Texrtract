// static/entities.js

$(document).ready(function() {
    var entities = JSON.parse(localStorage.getItem('detected_entities'));
    if (entities) {
        var entitiesTableBody = $('#entities-table tbody');
        entitiesTableBody.empty(); // Clear any existing rows

        entities.forEach(function(entity) {
            var row = $('<tr>');
            row.append($('<td>').text(entity.Score.toFixed(6)));
            row.append($('<td>').text(entity.Type));
            row.append($('<td>').text(entity.Text));
            row.append($('<td>').text(entity.BeginOffset));
            row.append($('<td>').text(entity.EndOffset));
            entitiesTableBody.append(row);
        });

        localStorage.removeItem('detected_entities'); // Clean up
    } else {
        $('#entities-table').hide();
        $('body').append('<p>No entities found. Please upload an image first.</p>');
    }
});
