var get_post = function (args, markup_func) {
    var url = "/api/post";
    url += urlEncode(args);
    $.get(url, function (data, status) {
        if (status == "success") {
            $(".post-item").fadeOut("slow");
            var container = $("<ul></ul>");
            for (var index in data.post) {
                container.append(markup_func(data.post[index]));
            }
            $("#post-container").html(container);
            $("#pagination-container").html(pagination_widget(data.page, data.pagesize, args, markup_func));
            $(".post-item").fadeIn("slow");
        }
        else {
            return ""
        }
    });
};
var get_tagscloud = function () {
    $.get("/api/tag", function (data, status) {
        if (status == "success") {
            var container = $("#tagscloud");
            var alpha = 0;
            for (var index in data) {
                cur = data[index].count;
                if (cur > alpha) {
                    alpha = cur;
                }
            }
            alpha = 108 / alpha;
            for (index in data) {
                container.append(tag_item_markup(data[index], alpha));
            }
            var tags = $(".tag");
            tags.fadeIn("slow");
            $("#post-container").css("height", "600px");
            tags.click(function () {
                var name = $(this).html();
                // tags.fadeOut("slow");
                get_post({page: 1, tag: name}, archive_item_markup);
            });
        }
    });
};
var urlEncode = function (param, key, count) {
    if (param == null) return '';
    var paramStr = '';
    var t = typeof (param);
    if (t == 'string' || t == 'number' || t == 'boolean') {
        if (count == 0) {
            paramStr += '?' + key + '=' + param;
        }
        else {
            paramStr += '&' + key + '=' + param;
        }
    }
    else {
        count = 0;
        for (var i in param) {
            var k = key == null ? i : key + (param instanceof Array ? '[' + i + ']' : '.' + i);
            paramStr += urlEncode(param[i], k, count);
            count += 1;
        }
    }
    return paramStr;
};
var pagination_widget = function (page, pagesize, args, markup_func) {
    var pagination = $("<ul class='pagination'></ul>");
    pagination.append("<li id='prev' type='button'>&laquo;</li>");
    pagination.append("<li id='cur'>" + page + "/" + pagesize + "</li>");
    pagination.append("<li id='next' type='button'>&raquo;</li>");
    if (page > 1) {
        pagination.children("#prev").addClass("active");
        pagination.children("#cur").addClass("active_prev");
        pagination.children("#prev").on("click", function () {
            args.page = page - 1;
            get_post(args, markup_func);
        });
    }
    if (page < pagesize) {
        pagination.children("#next").addClass("active");
        pagination.children("#cur").addClass("active_next");
        pagination.children("#next").on("click", function () {
            args.page = page + 1;
            get_post(args, markup_func);
        });
    }
    return pagination
};
var tag_item_markup = function (data, alpha) {
    var content = $("<a></a>");
    content.attr("class", "tag");
    content.attr("href", "#post-container");
    content.html(data.name);
    content.attr("style", "font-size: " + data.count * alpha + "px;display: none;");
    return content;
};
var post_item_markup = function (data) {
    var item = $("<li class=\"post-item\" style='display: none;'></li>");
    var item_article = $("<article class=\"post\"></article>");
    item_article.append($("<span class=\"post-time\"></span>").html(moment(data.timestamp).format("LL")));
    item_article.append($("<h3 class=\"post-title\"></h3>").html($("<a></a>").attr("href", data.link).html(data.title)));
    item_article.append($("<div class=\"post-summary\"></div>").html($("<p></p>").html(data.summary)));
    item.append("<div class='avatar'><img src='" + data.author.gravatar + "'></div><div class='author'>" + data.author.username + "</div>");
    item.append(item_article);
    return item;
};
var archive_item_markup = function (data) {
    var item = $("<li class=\"post-item\" style='display: none;'></li>");
    var item_article = $("<article class=\"archive-item\"></article>");
    item_article.append($("<div class=\"post-time\"></div>").html(moment(data.timestamp).format("DD MMM YY")));
    item_article.append($("<h3 class=\"post-title\"></h3>").html($("<a></a>").attr("href", data.link).html(data.title)));
    item.append(item_article);
    return item;
};
var setCookie = function (c_name, value, expiredays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate() + expiredays);
    document.cookie = c_name + "=" + escape(value) +
        ((expiredays == null) ? "" : ";expires=" + exdate.toGMTString())
};
var getCookie = function (c_name) {
    if (document.cookie.length > 0) {
        c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) c_end = document.cookie.length;
            return unescape(document.cookie.substring(c_start, c_end))
        }
    }
    return ""
};