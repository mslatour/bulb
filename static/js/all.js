$(function() {

    var Idea = Backbone.Model.extend({

        defaults: function() {
            return {
                title: "A great idea",
            };
        },

        // add trailing slash to request url
        // necessary for Django as Backbone does not add trailing slash
        url: function() {
            var origUrl = Backbone.Model.prototype.url.call(this);

            if (origUrl.substr(origUrl.length - 1) !== "/")
                origUrl += '/';
                
            return origUrl;
        },


        remove: function() {
            this.destroy();
        },

        initialize: function() {
            if (!this.get("title")) {
                this.set({"title": this.defaults().title});
            }
            this.selected = false;
        },

    });

    var IdeaView = Backbone.View.extend({
        tagName: 'tr',

        template: _.template($('script#ideaRowTpl').html()),

        events: {
            "click": "toggleSelected",
            "click button#id_delete": "remove",
            "click .verify button.yes": "removeVerifyTrue",
            "click .verify button.no": "removeVerifyFalse"
        },

        remove: function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();

            // replace button with verification stage buttons
            $(this.el).find('#id_delete').replaceWith($('script#verificationTpl').html());
        },

        removeVerifyTrue: function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();
            this.model.remove();
        },

        removeVerifyFalse: function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();
            this.render();
        },

        toggleSelected: function(event) {
            model = this.model;

            // switch 'selected' flag
            if (model.selected) {
                model.selected = false;
            } else {
                // deselect all other models
                model.collection.each(function(idea) {
                    idea.selected = false;
                });
                model.selected = true;
                // get neighbours
                this.getNeighbours();
            }

        },

        getNeighbours: function() {
            model = this.model;
            // deselect all other neighbours
            model.collection.each(function(idea) {
                idea.neighbour = false;
            });
            // get neighbours
            r = $.ajax({
                url: 'idea/' + this.model.id + '/neighbours/',
                type: 'GET',
                dataType: 'json',
                success: function(result) {
                    $.each(result, function(index, value) {
                        neighbour = model.collection.where(value)[0]
                        neighbour.neighbour = true;
                    });
                    // trigger change event on collection to rerender view
                    model.collection.trigger('change');
                }
            });
        },

        render: function() {
            self = this; // we need to reference the model from the inner scope of functions
            $(this.el).html(this.template(this.model.toJSON()));

            // make row drag- and droppable
            $(this.el).draggable({opacity: 0.5, distance: 20, helper: "clone"});
            $(this.el).droppable({
                hoverClass: "info",
                drop: function(event, ui) {
                    startNode = ui.draggable;
                    endNode = $(this);

                    startNodeID = startNode.find('td.idea-id').html();
                    endNodeID = endNode.find('td.idea-id').html();

                    $.ajax({
                        url: 'idea/' + startNodeID + '/neighbours/',
                        type: 'POST',
                        dataType: 'json',
                        data: {"neighbour": endNodeID * 1}, // convert from string to int, quite ugly
                        success: function(result) {
                            startNode.find('td .linked').html('<strong>Linked!</strong>').delay(500).animate({opacity: 0.0}, 800);
                            endNode.find('td .linked').html('<strong>Linked!</strong>').delay(500).animate({opacity: 0.0}, 800);
                            startNode.getNeighbours();
                        },
                    });
                },
            });

            // show selection by marking in green
            if (this.model.selected)
                $(this.el).addClass('success');

            if (this.model.neighbour)
                $(this.el).addClass('warning');

            return this;
        }   

    });

    var IdeaCollection = Backbone.Collection.extend({
        model: Idea,
        url: 'http://localhost:8000/idea/',

    });

    var IdeaListView = Backbone.View.extend({
        tagName: 'tbody',

        initialize: function(options) {
            this.ideas = new IdeaCollection();

            this.ideas.bind('reset', this.render, this);
            this.ideas.bind('add', this.render, this);
            this.ideas.bind('change', this.render, this);
            this.ideas.bind('remove', this.render, this);
            this.ideas.fetch();
        },


        addOne: function(idea) {
            this.$el.append(new IdeaView({model: idea}).render().el);
            return this;
        },

        addNew: function(idea) {
            var self = this;
            this.ideas.create(idea, {wait: true, success: function(model, response){
                console.log(response);
                console.log(model);
            }});
            return this;
        },

        render: function() {
            this.$el.html('');
            this.ideas.each(this.addOne, this);
            return this;

        }
    });


    var AppView = Backbone.View.extend({
        el: '#app',

        events: {
            "click #ideaForm button#addButton": "handleSubmit",
            "click #loginForm button#loginButton": "handleLogin",
            "keypress #ideaForm": "handleSubmitOnEnter",
        },

        handleLogin: function(event) {
          event.preventDefault();
          event.stopImmediatePropagation();
          alert("Login pressed!");
        },

        handleSubmit: function(event) {
            event.preventDefault();
            event.stopImmediatePropagation();
            var form = $('#ideaForm');

            var ideaData = {
                title: $(form).find('#id_title').val(),
            };

            this.ideaList.addNew(ideaData);

            return this;
        },

        handleSubmitOnEnter: function(event) {
            if (event.keyCode == 13) {
                return this.handleSubmit(event);
            }
        },

        initialize: function() {
            this.ideaList = new IdeaListView();
        },

        render: function() {
            this.$el.find('table').append(this.ideaList.render().el);
        },
    });

    var app = new AppView();
    app.render();

    /* */

});
