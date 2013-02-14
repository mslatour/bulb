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
            return origUrl += origUrl.endsWith('/') ? '' : '/';
        },


        remove: function() {
            this.destroy();
        },

        initialize: function() {
            if (!this.get("title")) {
                this.set({"title": this.defaults().title});
            }
        },

    });

    var IdeaView = Backbone.View.extend({
        tagName: 'tr',

        template: _.template($('script#ideaRowTpl').html()),

        events: {
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

        render: function() {
            $(this.el).html(this.template(this.model.toJSON()));
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
            "click #ideaForm button": "handleSubmit",
            "keypress #ideaForm": "handleSubmitOnEnter",
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

});
