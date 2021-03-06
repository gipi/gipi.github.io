---
layout: page
title: Tags
---

{% for post in site.posts %}
{% endfor %}

{% comment %}
Original code from <https://codinfox.github.io/dev/2015/03/06/use-tags-and-categories-in-your-jekyll-based-github-pages/>
=======================
The following part extracts all the tags from your posts and sort tags, so that you do not need to manually collect your tags to a place.
=======================
{% endcomment %}
{% assign rawtags = "" %}
{% for post in site.posts %}
    {% assign ttags = post.tags | join:'|' | append:'|' %}
    {% assign rawtags = rawtags | append:ttags %}
{% endfor %}
{% assign rawtags = rawtags | split:'|' | sort %}

{% comment %}
=======================
The following part removes duplicated tags and invalid tags like blank tag.
=======================
{% endcomment %}
{% assign tags = "" %}
{% for tag in rawtags %}
    {% if tag != "" %}
        {% if tags == "" %}
            {% assign tags = tag | split:'|' %}
        {% endif %}
        {% unless tags contains tag %}
            {% assign tags = tags | join:'|' | append:'|' | append:tag | split:'|' %}
        {% endunless %}
    {% endif %}
{% endfor %}

{% comment %}
=======================
The purpose of this snippet is to list all your posts posted with a certain tag.
=======================
{% endcomment %}
{% for tag in tags %}
<h2 id="{{ tag | slugify }}">{{ tag }}</h2>
    {% for post in site.posts %}
        {% if post.tags contains tag %}
 * [{{ post.title }}]({{ site.baseurl }}{{ post.url }}) / {{ post.date | date_to_string }}
{% comment %}
            {% for tag in post.tags %}
<a class="tag" href="#{{ tag | slugify }}">{{ tag }}</a>
            {% endfor %}
{% endcomment %}
        {% endif %}
    {% endfor %}
{% endfor %}
