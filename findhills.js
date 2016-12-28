
// This example adds a search box to a map, using the Google Place Autocomplete
// feature. People can enter geographical searches. The search box will return a
// pick list containing a mix of places and predicted search terms.

// This example requires the Places library. Include the libraries=places
// parameter when you first load the API. For example:
// <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places">
var map;
var postURL = "http://0.0.0.0";
// Recieved data and parts
var data;
var graph;
var origins;
var results;
var edgeHeights;
var nodeLatLongs;
var stoplights;
// Settings chosen from map
var useStoplights;
var maxDiversions;
// Results from JS mess
var maxesAndPaths;
var sortedMaxes;
// Stuff on map and for buttons
var polyline;
var marker;
var mapIteration;
var mapVelocity;
var params={};
window.location.search
  .replace(/[?&]+([^=&]+)=([^&]*)/gi, function(str,key,value) {
    params[key] = value;
  }
);
// I fuckin love one liners
// var sortedMaxesAndPaths = [];

function initAutocomplete() {
  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 33.77755, lng: -84.40075},
    zoom: 13,
    mapTypeId: 'roadmap'
  });

  // Create the search box and link it to the UI element.
  var input = document.getElementById('pac-input');
  var searchBox = new google.maps.places.SearchBox(input);
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);

  // Bias the SearchBox results towards current map's viewport.
  map.addListener('bounds_changed', function() {
    searchBox.setBounds(map.getBounds());
  });

  var markers = [];
  // Listen for the event fired when the user selects a prediction and retrieve
  // more details for that place.
  searchBox.addListener('places_changed', function() {
    var places = searchBox.getPlaces();

    if (places.length == 0) {
      return;
    }

    // Clear out the old markers.
    markers.forEach(function(marker) {
      marker.setMap(null);
    });
    markers = [];

    // For each place, get the icon, name and location.
    var bounds = new google.maps.LatLngBounds();
    places.forEach(function(place) {
      if (!place.geometry) {
        console.log("Returned place contains no geometry");
        return;
      }
      var icon = {
        url: place.icon,
        size: new google.maps.Size(71, 71),
        origin: new google.maps.Point(0, 0),
        anchor: new google.maps.Point(17, 34),
        scaledSize: new google.maps.Size(25, 25)
      };

      // Create a marker for each place.
      markers.push(new google.maps.Marker({
        map: map,
        icon: icon,
        title: place.name,
        position: place.geometry.location
      }));

      if (place.geometry.viewport) {
        // Only geocodes have viewport.
        bounds.union(place.geometry.viewport);
      } else {
        bounds.extend(place.geometry.location);
      }
    });
    map.fitBounds(bounds);
    rectangle.setBounds(bounds);
    rectangle.setMap(map);
    $("#hide-rectangle").prop('checked', false)
  });
  var originalRectBounds = {
    north: 33.7874,
    south: 33.7677,
    east: -84.3812,
    west: -84.4203
  };

  // Define the rectangle and set its editable property to true.
  rectangle = new google.maps.Rectangle({
    bounds: originalRectBounds,
    editable: true,
    draggable: true
  });

  rectangle.setMap(map);
  if (params['west'] != undefined
    && params['south'] != undefined
    && params['east'] != undefined
    && params['north'] != undefined) {
    var urlBounds = {
      west: parseFloat(params['west']),
      south: parseFloat(params['south']),
      east: parseFloat(params['east']),
      north: parseFloat(params['north'])
    };

    rectangle.setBounds(urlBounds);
    map.setCenter({
      lat: (urlBounds['north'] + urlBounds['south']) / 2,
      lng: (urlBounds['east'] + urlBounds['west']) / 2,
    });
  }
  // Add an event listener on the rectangle.
  // rectangle.addListener('bounds_changed', showNewRect);
  // Not needed?

  // Define an info window on the map.
  infoWindow = new google.maps.InfoWindow();
  polyline = new google.maps.Polyline({
    map: map,
    strokeColor: '#FF0000',
    strokeOpacity: 1.0,
    strokeWeight: 2
  });
  marker = new google.maps.Marker({
    map: map,
    title: "Start of path"
  })
  // polyline.setMap(map);
  // polyline.setPath([{lat: 33.7874, lng: -84.3812}, {lat: 33.7677, lng: -84.4203}])
}

$(document).ready(function() {


  $("#send").click(function() {
    var rectBounds = rectangle.getBounds().toJSON();
    useStoplights = $("#stoplights").prop('checked');
    var startSpeed = parseFloat($("#startSpeed").val());
    if (startSpeed == NaN) {
      startSpeed = 1.0;
    }
    maxDiversions = parseInt($("#diversions").val())
    if (maxDiversions == NaN) {
      maxDiversions = 2;
    }
    var findPaths = generateFindPaths()
    $("#send").prop('disabled', true);
    $("#status").html("Getting Map...");
    $.ajax({
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(rectBounds),
      //dataType: 'json',
      url: '/send_square/',
      success: function(inputData) {
        data = inputData;
        if (data == false) {
          $("#status").html("Request Rejected from OpenStreetMap API. "
            + "Consider donating so maybe one day I might have enough "
            + "money to locally host a US or world map on my own server.");
          $("#send").prop('disabled', false);
          return;
        }
        $("#share-box").val(postURL + "?" + $.param(rectBounds));
        console.log(data);
        graph = data["graph"];
        stoplights = data["stoplights"]
        nodeLatLongs = data["node_latlons"];
        edgeHeights = data["edge_heights"];
        $("#status").html("Got map! Finding routes...");
        $("#send").prop('disabled', false);
        origins = (useStoplights ? data["local_maxima"].
          concat(data["stoplights"]) : data["local_maxima"]);
        var paths = [];
        var maxVels = [];
        // TODO: Sort origins?
        for (var i = 0, len = origins.length; i < len; i++) { // TODO len
          // forEach is not async, thank god
          // actual for loop is faster lol; I don't think it matters
          origin = origins[i]
          var newPathsAndMaxes = findPaths(
            origin, startSpeed, [], startSpeed
            );
          // console.log(findPaths)
          // console.log(newPathsAndMaxes[0])
          // console.log(newPathsAndMaxes[1])
          paths = paths.concat(newPathsAndMaxes[0]);
          maxVels = maxVels.concat(newPathsAndMaxes[1]);
        };
        maxesAndPaths = {};
        if (paths.length != maxVels.length) {
          console.log("Something's gone horribly wrong." +
            " Paths is " + paths.length + " long and maxVels is " +
            maxVels.length + "long.");
        }
        for (var i = 0, len = paths.length; i < len; i++) {
          if (maxesAndPaths[maxVels[i]] == undefined) {
            maxesAndPaths[maxVels[i]] = [paths[i]];
          } else {
            maxesAndPaths[maxVels[i]] =
              maxesAndPaths[maxVels[i]].concat([paths[i]]);
          }
        }
        sortedMaxes = Object.keys(maxesAndPaths).sort(function (a, b) {
          return (parseFloat(b) - parseFloat(a));
        }) // TODO change b to nodeHeights(b)
        console.log(sortedMaxes);
        var resultContent = "";
        for (var i = 0, len = sortedMaxes.length; i < len; i++) {
          resultContent += "<h3>" + sortedMaxes[i] + "m/s </h3>"
          for (var j = 0, len2 = maxesAndPaths[sortedMaxes[i]].length;
            j < len2; j++) {
            resultContent +=
              "<div class='path' data-max='" +
              sortedMaxes[i] + "' data-iteration=" + j + ">Path " +
              j + "</div>";
          }

        }
        $("#result-container").html(resultContent);
        mapIteration = 0; // Index 0
        mapVelocity = sortedMaxes[0]; // Show fastest path first
        showPath(maxesAndPaths[mapVelocity][mapIteration], mapVelocity);
        updateButtons();
        $("#hide-rectangle").prop('checked', true);
        rectangle.setMap(null);
        $("#status").html("Found routes.");
        // $("#result-container").accordion({
        //   heightStyle: "content"
        // });
      },
      error: function(jqXHR, textStatus, errorThrown) {
        $("#status").html(
          "Server Error " + textStatus + " " + errorThrown
          );
        $("#send").prop("disabled", false);
      }
    });
    return false; //recommended by tutsplus for some reason
    // https://code.tutsplus.com/tutorials/10-ways-to-instantly-increase-your-jquery-performance--net-5551
    //console.log(rectBounds);
  });
  $("#result-container").on("click", ".path", function() {
    var path = maxesAndPaths[$(this).data("max")][$(this).data("iteration")];
    showPath(path, $(this).data("max"));
    mapIteration = $(this).data("iteration");
    mapVelocity = $(this).data("max");
    updateButtons();
  });

  $("#hide-rectangle").change(function() {
    if ($(this).prop("checked")) {
      rectangle.setMap(null);
    } else {
      rectangle.setMap(map);
    }
  })

  $("#skip-back").prop('disabled', true);
  $("#back").prop('disabled', true);
  $("#forward").prop('disabled', true);
  $("#skip-forward").prop('disabled', true);

  $("#skip-back").click(function() {
    mapIteration = 0;
    mapVelocity = sortedMaxes[sortedMaxes.indexOf(mapVelocity) - 1]
    showPath(maxesAndPaths[mapVelocity][mapIteration], mapVelocity);
    updateButtons();
  });
  $("#back").click(function() {
    mapIteration -= 1;
    showPath(maxesAndPaths[mapVelocity][mapIteration], mapVelocity);
    updateButtons();
  });
  $("#forward").click(function() {
    mapIteration += 1;
    showPath(maxesAndPaths[mapVelocity][mapIteration], mapVelocity);
    updateButtons();
  });
  $("#skip-forward").click(function() {
    mapIteration = 0;
    mapVelocity = sortedMaxes[sortedMaxes.indexOf(mapVelocity) + 1]
    showPath(maxesAndPaths[mapVelocity][mapIteration], mapVelocity);
    updateButtons();
  });
  $("#share-box").focus(function(){
    $(this).one('mouseup', function(event){
      event.preventDefault();
    }).select();
  });
  $("#copy-button").click(function() {
    var copyTextarea = document.querySelector('#share-box');
    copyTextarea.select();
    document.execCommand('copy');
  });
});
function updateButtons() {
  if (mapVelocity == sortedMaxes[0]) {
    $("#skip-back").prop('disabled', true);
  } else {
    $("#skip-back").prop('disabled', false);
  }
  if (mapIteration == 0) {
    $("#back").prop('disabled', true);
  } else {
    $("#back").prop('disabled', false);
  }
  if (mapIteration >= maxesAndPaths[mapVelocity].length - 1)
  {
    $("#forward").prop('disabled', true);
  } else {
    $("#forward").prop('disabled', false);
  }
  if (mapIteration >= sortedMaxes.length - 1) {
    $("#skip-forward").prop('disabled', true);
  } else {
    $("#skip-forward").prop('disabled', false);
  }

}
function generateFindPaths() {
  function findPathsRecursive(start, vel, path, maxVel) {
    path.push(start);
    if (
      vel == 0
      || (useStoplights && stoplights.indexOf(start) != -1 && path.length > 1)
      || !(graph[start].some(function(neighbor) {
        return path.indexOf(neighbor) == -1;
        })) // TODO check if correct
      ) {
      return [[path], [maxVel]];
    }
    var paths = []
    var maxVels = []
    var neighbors = graph[start];
    // neighbors.sort(sortBySlopeReversed(start, a, b)) // TODO enable
    for(
      var i = 0, len = neighbors.length, found = 0;
      found < maxDiversions && i < len;
      i++) {
      var neighbor = neighbors[i];
      if (path.indexOf(neighbor) == -1) {
        found ++;
        var velAndMaxVel = rideDownNode(start, neighbor, vel, maxVel);
        var newPathsAndNewMaxes = findPathsRecursive(
          neighbor, velAndMaxVel[0], path.slice(), velAndMaxVel[1]
          );
        paths = paths.concat(newPathsAndNewMaxes[0]);
        maxVels = maxVels.concat(newPathsAndNewMaxes[1]);
      }
    };
    // console.log(paths);
    return [paths, maxVels];
  }
  function findPathsBreadthFirst(start, vel, path, maxVel) {
    var pathsToReturn = [];
    var maxVelsToReturn = [];
    var pathsToExtend = [[start]];
    var maxVels = [maxVel]
    var vels = [vel]
    while (pathsToExtend.length != 0) {
      var pathToExtend = pathsToExtend.shift(); // Remove & return arr[0]
      var pathsMaxVel = maxVels.shift(); // all are pop in df
      var pathsVel = vels.shift();
      var start = pathToExtend[pathToExtend.length - 1];
      var neighbors = graph[start];
      // neighbors.sort(sortBySlope(start, a, b)) // TODO enable // DF reverse
      for(
        var i = 0, len = neighbors.length, found = 0;
        found < maxDiversions && i < len;
        i++)
      {
        var neighbor = neighbors[i];
        var newPath = pathToExtend.concat(neighbor);
        if (pathToExtend.indexOf(neighbor) == -1) {
          found ++;
          var velAndMaxVel =
            rideDownNode(start, neighbor, pathsVel, pathsMaxVel);
          if (
            velAndMaxVel[0] == 0
            || (useStoplights
              && stoplights.indexOf(neighbor) != -1 // TODO make less stupid
              && newPath.length > 1)
            || !(graph[neighbor].some(function(otherNeighbor) {
              return newPath.indexOf(otherNeighbor) == -1;
              })) // TODO check if correct
            )
          {
            pathsToReturn.push(newPath);
            maxVelsToReturn.push(velAndMaxVel[1]);
          } else {
            pathsToExtend.push(newPath);
            vels.push(velAndMaxVel[0]);
            maxVels.push(velAndMaxVel[1]);
          }
        }
      }
    }
    return [pathsToReturn, maxVelsToReturn];
    // TODO test
  }
  function findPathsDepthFirst(start, vel, path, maxVel) {
    var pathsToReturn = [];
    var maxVelsToReturn = [];
    var pathsToExtend = [[start]];
    var maxVels = [maxVel]
    var vels = [vel]
    while (pathsToExtend.length != 0) {
      var pathToExtend = pathsToExtend.pop();
      var pathsMaxVel = maxVels.pop();
      var pathsVel = vels.pop();
      var start = pathToExtend[pathToExtend.length - 1];
      var neighbors = graph[start];
      // neighbors.sort(sortBySlopeReversed(start, a, b)) // TODO enable
      for(
        var i = 0, len = neighbors.length, found = 0;
        found < maxDiversions && i < len;
        i++)
      {
        var neighbor = neighbors[i];
        var newPath = pathToExtend.concat(neighbor);
        if (pathToExtend.indexOf(neighbor) == -1) {
          found ++;
          var velAndMaxVel =
            rideDownNode(start, neighbor, pathsVel, pathsMaxVel);
          if (
            velAndMaxVel[0] == 0
            || (useStoplights
              && stoplights.indexOf(neighbor) != -1 // TODO make less stupid
              && newPath.length > 1)
            || !(graph[neighbor].some(function(otherNeighbor) {
              return newPath.indexOf(otherNeighbor) == -1;
              })) // TODO check if correct
            )
          {
            pathsToReturn.push(newPath);
            maxVelsToReturn.push(velAndMaxVel[1]);
          } else {
            pathsToExtend.push(newPath);
            vels.push(velAndMaxVel[0]);
            maxVels.push(velAndMaxVel[1]);
          }
        }
      }
    }
    return [pathsToReturn, maxVelsToReturn];
    // TODO test
  }
  searchMethod = $("#search-method").val()
  if (searchMethod == "recursive") {
    return findPathsRecursive;
  }
  if (searchMethod == "depth-first") {
    return findPathsDepthFirst;
  }
  if (searchMethod == "breadth-first") {
    return findPathsBreadthFirst;
  }
  return findPathsBreadthFirst; // should never run
}
function sortBySlope(start, a, b) {
  // TODO
}
function sortBySlopeReversed(start, a, b) {
  return b - a; // TODO
}
function rideDownNode(src, dest, vel, maxVel) {
  if (vel > maxVel) {
    maxVel = vel;
  }
  var distInternode = latLng2Dist(
    nodeLatLongs[src][0],
    nodeLatLongs[src][1],
    nodeLatLongs[dest][0],
    nodeLatLongs[dest][1]
    );
  var dist = distInternode / edgeHeights["(" + src + ", " + dest + ")"].length;
  var edge = edgeHeights["(" + src + ", " + dest + ")"];
  for (var i = 1, len = edge.length; i < len; i++) {
    var dh = edge[i] - edge[i - 1];
    vel = newVelocity(vel, dh, dist);
    if (vel > maxVel) {
      maxVel = vel;
    }
    if (vel == 0) {
      break;
    }
  }
  return [vel, maxVel];
}

function latLng2Dist(lat1Raw, lng1Raw, lat2Raw, lng2Raw) {
  // This thing assumes the earth is spherical, which I think
  // hurts us less than the float -> decimal -> float conversion
  // that we're dealing with in JSON :/
  // The decimal is only accurate to .000001 deg ~ 1.1 m :'(
  var lat1 = lat1Raw * Math.PI / 180;
  // Original Python converts raw to float... IDK if we need to.
  var lng1 = lng1Raw * Math.PI / 180;
  var lat2 = lat2Raw * Math.PI / 180;
  var lng2 = lng2Raw * Math.PI / 180;
  // Radius of earth in meters, could use more precision if we
  // can figure it out for the US average.
  var radius = 6373000.0;
  var dlng = lng2 - lng1;
  var dlat = lat2 - lat1;
  var a = (Math.sin(dlat / 2) * Math.sin(dlat / 2) + Math.cos(lat1)
    * Math.cos(lat2) * Math.sin(Math.pow(dlng / 2, 2)));
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  var distance = radius * c;
  return distance;
}

// Constants, probably to be modded by UI onclick
var g = -9.81 // accelertion due to gravity, m/s
var dragC = .6 // drag coefficient of human body
var crossA = .68 // Cross-sectional area of human body
var mass = 80 // kg
var frictC = .03 // Coefficient of friction

function newVelocity(v0, dh, dist) {
  if (v0 == 0) {
    return 0;
  }
  var theta = Math.atan2(dh, dist);
  var a = (
    g * Math.sin(theta)
    - (1.225 * dragC * crossA * v0 * v0) / (2 * mass)
    + (g * frictC * Math.cos(theta))
    );
  // Total Acceleration = grav, air resistance, rolling friction resistance
  // Assumes final velocity causes about the amount of air resistance as
  // inital velocity TODO: Make more classically perfect by integrating
  var velSquared = 2 * a * Math.sqrt(dist * dist + dh * dh) + v0 * v0;
  if (velSquared > 0) {
    return Math.sqrt(velSquared);
  }
  return 0;
}
function showPath(path, maxVel) {
  $("#maxVel-container").html("Max Velocity: " + maxVel);
  var googlePath = [];
  for (var i = 0, len = path.length; i < len; i++) {
    googlePath.push({
      lat: nodeLatLongs[path[i]][0],
      lng: nodeLatLongs[path[i]][1]
    });
    // if (i < len-1) {
    //   console.log(path[i + 1] in graph[path[i]]);
    // }
  }
  polyline.setPath(googlePath);
  marker.setPosition({
    lat: nodeLatLongs[path[0]][0],
    lng: nodeLatLongs[path[0]][1]
  });
  map.setCenter({
    lat: nodeLatLongs[path[0]][0],
    lng: nodeLatLongs[path[0]][1]
  });
}