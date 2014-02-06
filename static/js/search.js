/**
 *
 *
 */

app.controller("SeachController", ["$scope", "$location", "$http", "$timeout",
    function ($scope, $location, $http, $timeout) {

        var index_names = {
            "eng": "English",
            "eng_gen": "English (generalized)",
            "rus": "Russian",
            "rus_gen": "Russian (generalized)",
            "spa": "Spanish"
        };

        var query = $location.search().query;
        var index = $location.search().index;
        var mfreq = $location.search().mfreq;
        var rpage = $location.search().rpage;
        var rtype = $location.search().rtype;
        var debug = $location.search().debug;

        if (typeof query == "undefined") query = "";
        if (typeof index == "undefined") index = "eng";
        if (typeof mfreq == "undefined") mfreq = "0";
        if (typeof rpage == "undefined") rpage = "1";
        if (typeof rtype == "undefined") rtype = "*";

        $scope.query = {
            "query": query,
            "index": index,
            "mfreq": mfreq,
            "rpage": rpage,
            "rtype": rtype,
            "debug": debug,
            "index_name": index_names[index]
        };

        var makePagination = function(search_result) {
            var pages = [];
            var indexes = [];
            if (search_result.page != 1) {
              pages.push({index:1, text:"First", css_class:""});
              pages.push({index:search_result.page - 1, text:"Previous", css_class:""});
            }
            var total = search_result.pages;
            var window = 5;
            var begin = Math.max(search_result.page - window - 1, 0);
            var end = Math.min(search_result.page + window, search_result.pages - 1);
            for (var i=begin+1; i<=end+1; ++i){
                if (i == search_result.page)
                    pages.push({index:i, text:i+"", css_class:"active"});
                else
                    pages.push({index:i, text:i+"", css_class:""});
            }
            if (search_result.page != search_result.pages) {
              pages.push({index:search_result.page+1, text:"Next", css_class:""});
              pages.push({index:search_result.pages, text:"Last", css_class:""});
            }
            return pages;
        };

        if (query != "") {
            $http({
                method: "GET",
                url: "/find",
                params: {
                    "query": query,
                    "index": index,
                    "mfreq": mfreq,
                    "rpage": rpage,
                    "rtype": rtype
                }
            }).success(function (data, status, headers, config) {
                    $scope.search_result = data;
                    $scope.pagination = makePagination(data);
                    $timeout(function(){
                        $(".show-popover").popover({
                            "html": true
                        });
                    }, 0, false);
            }).error(function (data, status, headers, config) {

            });
        }

        $scope.SetIndex = function(index) {
            $scope.query.index = index;
            $scope.Find();
        };

        $scope.Find = function (page) {
            if (typeof page != "undefined")
                $scope.query.rpage = page;
            else
                $scope.query.rpage = "1";
            $location.path("/").search({
                "query": $scope.query.query,
                "index": $scope.query.index,
                "mfreq": $scope.query.mfreq,
                "rpage": $scope.query.rpage,
                "rtype": $scope.query.rtype
            });
        };

        $scope.ShowRelTypeHelp = function() {
            $("#RelTypeHelp").modal();
        };
        $scope.ShowFreqHelp = function() {
            $("#FreqHelp").modal();
        };


}]);