$(function() {

    var Idea = Backbone.Model.extend({

        defaults: function() {
            return {
                title: "A great idea",
            };
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

        remove: function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();
            this.model.remove();
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
            this.ideas.fetch({success: function() {
                console.log(app.ideaList.ideas.models)
             }});
        },


        addOne: function(idea) {
            this.$el.append(new IdeaView({model: idea}).render().el);
            return this;
        },

        addNew: function(idea) {
            this.ideas.create(idea, {success: function(post){ console.log(post.toJSON()); }});
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
            "click #ideaForm :submit": "handleSubmit",
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
